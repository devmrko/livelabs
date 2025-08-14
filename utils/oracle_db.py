import oracledb
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    _pool = None

    @classmethod
    def initialize_pool(cls):
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_DSN = os.getenv("DB_DSN")
        WALLET_LOCATION = os.getenv("WALLET_LOCATION")
        TNS_ADMIN = os.getenv("TNS_ADMIN")
        PEM_PASSPHRASE = os.getenv("PEM_PASSPHRASE")

        if cls._pool is None:
            if not all([DB_USER, DB_PASSWORD, DB_DSN]):
                logger.error("DATABASE_MANAGER: Database credentials (DB_USER, DB_PASSWORD, DB_DSN) are not fully set. Pool not initialized.")
                raise ValueError("Database credentials are not properly configured.")
            
            pool_min = 2
            pool_max = 5
            pool_increment = 1
            try:
                logger.info(f"DATABASE_MANAGER: Initializing Oracle DB connection pool for DSN: {DB_DSN}")
                # Ensure wallet_location and PEM_PASSPHRASE are used if provided
                pool_params = {
                    "user": DB_USER,
                    "password": DB_PASSWORD,
                    "dsn": DB_DSN,
                    "min": pool_min,
                    "max": pool_max,
                    "increment": pool_increment,
                }
                if WALLET_LOCATION:
                    pool_params["config_dir"] = WALLET_LOCATION
                    pool_params["wallet_location"] = WALLET_LOCATION
                    pool_params["wallet_password"] = PEM_PASSPHRASE # If wallet is encrypted
                
                cls._pool = oracledb.create_pool(**pool_params)
                logger.info(f"DATABASE_MANAGER: Connection pool initialized. Min: {pool_min}, Max: {pool_max}")
            except oracledb.Error as e:
                logger.error(f"DATABASE_MANAGER: Error initializing connection pool: {e}")
                cls._pool = None # Ensure pool is None if initialization fails
                raise

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            cls.initialize_pool()
        return cls._pool
    
    @classmethod
    def reset_pool(cls):
        """Reset the connection pool if there are issues"""
        try:
            if cls._pool:
                cls._pool.close()
                logger.info("DATABASE_MANAGER: Connection pool closed for reset")
        except Exception as e:
            logger.error(f"DATABASE_MANAGER: Error closing pool for reset: {e}")
        finally:
            cls._pool = None
            logger.info("DATABASE_MANAGER: Connection pool reset, will reinitialize on next use")

    def get_connection(self):
        pool = self.get_pool()
        if pool:
            try:
                # logger.debug("DATABASE_MANAGER: Acquiring connection from pool.")
                return pool.acquire()
            except oracledb.Error as e:
                logger.error(f"DATABASE_MANAGER: Error acquiring connection from pool: {e}")
                raise
            except OSError as e:
                logger.error(f"DATABASE_MANAGER: OS Error acquiring connection from pool: {e}")
                raise
            except Exception as e:
                logger.error(f"DATABASE_MANAGER: Unexpected error acquiring connection from pool: {e}")
                raise
        else:
            logger.error("DATABASE_MANAGER: Connection pool is not available.")
            raise RuntimeError("Database connection pool is not initialized.")

    def release_connection(self, connection):
        pool = self.get_pool()
        if pool and connection:
            try:
                # logger.debug("DATABASE_MANAGER: Releasing connection to pool.")
                pool.release(connection)
            except oracledb.Error as e:
                logger.error(f"DATABASE_MANAGER: Error releasing connection to pool: {e}")
                # Don't raise, just log the error
            except OSError as e:
                logger.error(f"DATABASE_MANAGER: OS Error releasing connection to pool: {e}")
                # Don't raise, just log the error
            except Exception as e:
                logger.error(f"DATABASE_MANAGER: Unexpected error releasing connection to pool: {e}")
                # Don't raise, just log the error

    def execute_query(self, sql_query, params=None, fetch_one=False, fetch_all=False, commit=False, is_ddl=False, input_types=None):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # logger.debug(f"DATABASE_MANAGER: Executing query: {sql_query} with params: {params}")
            
            if input_types: # Set input types if provided
                cursor.setinputsizes(**input_types)
                # logger.debug(f"DATABASE_MANAGER: Set input types: {input_types}")

            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)

            result = None
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            
            rowcount = cursor.rowcount # Store rowcount before cursor is closed

            if commit or is_ddl: # DDL statements often require commit or have auto-commit
                conn.commit()
                # logger.debug(f"DATABASE_MANAGER: Query committed. SQL: {sql_query[:100]}...")
            
            cursor.close()
            # For fetch operations, result includes data. For DML, rowcount is more relevant.
            return result if (fetch_one or fetch_all) else rowcount
        
        except oracledb.Error as oe:
            logger.error(f"DATABASE_MANAGER: Oracle DB error executing query: {sql_query[:100]}... Error: {oe}")
            if conn and not is_ddl: # Don't rollback DDL typically
                try:
                    conn.rollback()
                except Exception as r_err:
                    logger.error(f"DATABASE_MANAGER: Error during rollback: {r_err}")
            raise # Re-raise the original Oracle error to be handled by the caller
        except OSError as oe:
            logger.error(f"DATABASE_MANAGER: OS error executing query: {sql_query[:100]}... Error: {oe}")
            if conn and not is_ddl:
                try:
                    conn.rollback()
                except Exception as r_err:
                    logger.error(f"DATABASE_MANAGER: Error during rollback: {r_err}")
            raise # Re-raise the OS error
        except Exception as e:
            logger.error(f"DATABASE_MANAGER: Unexpected error executing query: {sql_query[:100]}... Error: {e}")
            if conn and not is_ddl:
                try:
                    conn.rollback()
                except Exception as r_err:
                    logger.error(f"DATABASE_MANAGER: Error during rollback: {r_err}")
            raise # Re-raise the unexpected error
        finally:
            if conn:
                try:
                    self.release_connection(conn)
                except Exception as e:
                    logger.error(f"DATABASE_MANAGER: Error in finally block releasing connection: {e}")
                    # Don't raise, just log the error
                        # Don't raise, just log the error
        
        # If we get here, all retries failed
        if last_error:
            raise last_error

    def execute_clob_insert_or_update(self, sql_query, params_dict_with_clob_fields, clob_fields_and_values):
        """ 
        Handles insert/update with CLOB data.
        clob_fields_and_values: a dict like {'clob_column_name': 'large string data'}
        params_dict_with_clob_fields: all other bind variables for the query.
                                     CLOB fields in this dict should be placeholder LOB objects.
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Create LOB objects for CLOB fields
            lob_vars = {}
            for field_name, data_string in clob_fields_and_values.items():
                lob_var = cursor.createlob(oracledb.DB_TYPE_CLOB)
                lob_var.write(data_string if data_string is not None else "") # Handle None by writing empty string
                lob_vars[field_name] = lob_var
            
            # Update the main params dictionary with these LOB variables
            final_params = {**params_dict_with_clob_fields, **lob_vars}
            
            # logger.debug(f"DATABASE_MANAGER: Executing CLOB DML: {sql_query} with params containing LOBs for keys: {list(lob_vars.keys())}")
            cursor.execute(sql_query, final_params)
            rowcount = cursor.rowcount
            conn.commit()
            cursor.close()
            # logger.debug(f"DATABASE_MANAGER: CLOB DML committed. Rows affected: {rowcount}")
            return rowcount
        except oracledb.Error as oe:
            logger.error(f"DATABASE_MANAGER: Oracle DB error during CLOB DML: {sql_query[:100]}... Error: {oe}")
            if conn: conn.rollback()
            raise
        except Exception as e:
            logger.error(f"DATABASE_MANAGER: Unexpected error during CLOB DML: {sql_query[:100]}... Error: {e}")
            if conn: conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)

    @classmethod
    def close_pool(cls):
        if cls._pool:
            try:
                logger.info("DATABASE_MANAGER: Closing connection pool.")
                cls._pool.close(force=True) # force=True can be used to close busy connections too
                cls._pool = None
            except oracledb.Error as e:
                logger.error(f"DATABASE_MANAGER: Error closing connection pool: {e}")
        else:
            logger.info("DATABASE_MANAGER: Connection pool was not initialized or already closed.")
