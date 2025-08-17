# LiveLabs MCP Services Streamlit App

A reactive and interactive Streamlit application that provides a user-friendly interface for all LiveLabs MCP services.

## Features

### 🚀 **Reactive Service Management**
- **Real-time Service Status**: Monitor all MCP services with live status indicators
- **One-Click Start/Stop**: Start or stop individual services or all services at once
- **Service Health Monitoring**: Visual indicators for connected, starting, error, and disconnected states

### 🔍 **Semantic Search Interface**
- **Natural Language Queries**: Search LiveLabs workshops using natural language
- **Configurable Parameters**: Adjust top-k results and similarity thresholds
- **Quick Search Examples**: Pre-built search examples for common queries
- **Real-time Results**: Instant search results with detailed workshop information

### 👥 **User Profile Management**
- **User Lookup**: Find users by ID with complete profile information
- **Skill-Based Search**: Search users by specific skills and experience levels
- **User Statistics**: Comprehensive statistics about users and skills
- **Interactive Results**: Expandable user profiles with detailed skill information

### 📈 **Skills & Progression Analysis**
- **Natural Language Queries**: Ask questions about user skills and progression
- **Example Queries**: Pre-built examples for common skill-related questions
- **Progression Tracking**: Analyze user skill development over time
- **AI-Powered Insights**: Oracle SELECT AI integration for intelligent queries

### 📊 **Analytics Dashboard**
- **Service Overview**: Real-time status of all MCP services
- **Data Metrics**: Key performance indicators for LiveLabs data
- **Skills Distribution**: Visual charts showing skill popularity
- **Recent Activity**: Live feed of user activities and skill updates

## Installation

1. **Install Dependencies**:
```bash
pip install -r requirements_streamlit.txt
```

2. **Configure Environment**:
Ensure your `.env` file is properly configured with database credentials.

3. **Start the App**:
```bash
streamlit run streamlit_livelabs_app.py
```

## Usage

### 🎯 **Getting Started**

1. **Launch the App**: Open your browser to the Streamlit URL (usually `http://localhost:8501`)

2. **Start Services**: Use the sidebar to start the MCP services you need:
   - LiveLabs Semantic Search
   - LiveLabs User Profiles  
   - LiveLabs User Skills & Progression

3. **Navigate Tabs**: Use the main tabs to access different functionalities:
   - **Semantic Search**: Search workshops
   - **User Profiles**: Manage user data
   - **Skills & Progression**: Analyze skills
   - **Analytics Dashboard**: View metrics

### 🔍 **Semantic Search**

1. **Enter Query**: Type a natural language search query
2. **Adjust Parameters**: Set top-k results and similarity threshold
3. **Search**: Click "Search Workshops" to get results
4. **Quick Examples**: Use pre-built examples for instant results

**Example Queries**:
- "machine learning"
- "big data service"
- "cloud computing"
- "security and compliance"

### 👥 **User Profiles**

1. **Find User**: Enter a user ID to get complete profile
2. **Search by Skill**: Find users with specific skills
3. **Get Statistics**: View comprehensive user statistics

**Features**:
- User profile lookup
- Skill-based user search
- Experience level filtering
- User statistics and analytics

### 📈 **Skills & Progression**

1. **Natural Language Queries**: Ask questions about skills and progression
2. **Example Queries**: Use pre-built examples
3. **AI-Powered Analysis**: Get intelligent insights from Oracle SELECT AI

**Example Queries**:
- "what kinds of skill John Smith have, and how good are those"
- "show me users with expert level machine learning skills"
- "find users who have progressed from beginner to expert"
- "who are the most skilled users"

### 📊 **Analytics Dashboard**

1. **Service Status**: Monitor all MCP service connections
2. **Data Overview**: View key metrics and trends
3. **Skills Distribution**: Visualize skill popularity
4. **Recent Activity**: Track user activities

## Architecture

### **Reactive Design**
- **Real-time Updates**: Service status updates automatically
- **Interactive Elements**: Responsive UI with immediate feedback
- **State Management**: Persistent session state for service management

### **Service Integration**
- **MCP Service Manager**: Handles service lifecycle management
- **Process Management**: Starts/stops MCP services as subprocesses
- **Status Monitoring**: Real-time health checks for all services

### **Data Flow**
```
User Input → Streamlit UI → MCP Service Manager → MCP Services → Database → Results → UI Display
```

## Customization

### **Adding New Services**
1. Add service configuration to `MCPServiceManager.services`
2. Create corresponding tab and functionality
3. Add simulation functions for testing

### **Modifying UI**
- Custom CSS in the `st.markdown` section
- Tab organization in the main function
- Component layout using `st.columns`

### **Extending Functionality**
- Replace simulation functions with actual MCP calls
- Add new data visualization components
- Integrate additional data sources

## Troubleshooting

### **Common Issues**

1. **Service Won't Start**:
   - Check if Python path is correct
   - Verify MCP dependencies are installed
   - Check `.env` configuration

2. **Connection Errors**:
   - Ensure database credentials are correct
   - Check network connectivity
   - Verify service files exist

3. **UI Not Responsive**:
   - Refresh the browser page
   - Check browser console for errors
   - Restart Streamlit app

### **Debug Mode**
Run with debug information:
```bash
streamlit run streamlit_livelabs_app.py --logger.level debug
```

## Development

### **Local Development**
1. Install development dependencies
2. Run in development mode
3. Use hot reload for changes

### **Testing**
- Test each service individually
- Verify UI responsiveness
- Check error handling

### **Deployment**
- Deploy to Streamlit Cloud
- Configure environment variables
- Set up service monitoring

## Security

- **Environment Variables**: Sensitive data stored in `.env`
- **Service Isolation**: Each MCP service runs in separate process
- **Input Validation**: All user inputs are validated
- **Error Handling**: Comprehensive error handling and logging

## Performance

- **Lazy Loading**: Services start only when needed
- **Caching**: Session state for service management
- **Efficient Queries**: Optimized database queries
- **Responsive UI**: Fast loading and interaction

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify configuration
4. Test individual components

---

**🚀 Ready to explore LiveLabs data with the power of MCP services!**
