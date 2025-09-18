# AI-Powered UAV Mission Planning and Risk Assessment

A comprehensive web application that enables operators to design UAV missions on an interactive map, uses machine learning to assess mission risk, and suggests safer, optimized routes with real-time simulation capabilities.

## 🚁 Features

### Core Functionality
- **Interactive Map-Based Mission Planning**: Draw waypoints on a map interface
- **AI-Powered Risk Assessment**: XGBoost-based ML model for risk scoring
- **Route Optimization**: A* algorithm with risk-aware cost functions
- **Real-Time Simulation**: Physics-based UAV flight simulation
- **Risk Heatmaps**: Visual representation of risk factors across the map
- **No-Fly Zone Integration**: Automatic detection and avoidance of restricted areas

### Risk Assessment Categories
- **Weather Risk**: Wind speed, gusts, and weather severity
- **Battery Risk**: Energy consumption and safety margins
- **Airspace Risk**: Proximity to no-fly zones and restricted areas
- **Terrain Risk**: Obstacle density and terrain complexity
- **Route Risk**: Mission length and complexity factors
- **Altitude Risk**: Flight altitude considerations

### Technical Features
- **Explainable AI**: SHAP-based risk explanations
- **Real-Time Weather Integration**: Live weather data for accurate risk assessment
- **Mission History**: Save and retrieve previous missions
- **Performance Analytics**: Detailed mission metrics and statistics

## 🏗️ Architecture

```
├── frontend/           # React.js web application
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── hooks/      # Custom React hooks
│   │   └── App.js      # Main application
│   └── package.json    # Frontend dependencies
├── backend/            # FastAPI backend service
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── models/     # Data models and ML components
│   │   ├── services/   # Business logic services
│   │   └── core/       # Database and configuration
│   └── requirements.txt
├── ml/                 # Machine learning components
│   ├── data/           # Training data and generators
│   ├── models/         # Trained ML models
│   └── notebooks/      # Analysis and experimentation
├── sim/                # Simulation components
│   ├── scenarios/      # Sample mission scenarios
│   └── run_simulation.py
└── docs/               # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-powered-drone-mission-planning
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Train the ML model
   python ml/train_model.py
   
   # Start the backend server
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Setup (Alternative)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📊 Usage

### Mission Planning
1. **Start Planning**: Click "Start Planning" to begin adding waypoints
2. **Add Waypoints**: Click on the map to add waypoints for your mission
3. **Configure Settings**: Set battery capacity, max speed, and altitude
4. **Optimize Route**: Click "Optimize Route" to get AI-suggested safer path
5. **Review Analysis**: Check risk breakdown and warnings

### Simulation
1. **Run Simulation**: After planning, click "Run Simulation"
2. **Watch Playback**: Observe the UAV following the optimized route
3. **Monitor Metrics**: Track battery, speed, and risk levels in real-time

### Risk Analysis
1. **View Heatmap**: Toggle risk heatmap overlay on the map
2. **Check Warnings**: Review risk warnings and recommendations
3. **Examine Breakdown**: Understand risk factors contributing to the score

## 🔧 API Endpoints

### Mission Planning
- `POST /api/missions/plan` - Plan a new mission with risk assessment
- `GET /api/missions/` - List all saved missions
- `GET /api/missions/{mission_id}` - Get specific mission details

### Simulation
- `POST /api/missions/simulate` - Run mission simulation
- `GET /api/missions/{mission_id}/simulation` - Get simulation results

### Map Data
- `GET /api/map/risk-heatmap` - Get risk heatmap data
- `GET /api/map/no-fly-zones` - Get no-fly zone information
- `GET /api/map/weather` - Get weather data for location

## 🤖 Machine Learning

### Model Architecture
- **Algorithm**: XGBoost Classifier
- **Features**: 12 risk-related features
- **Training Data**: 10,000 synthetic mission scenarios
- **Performance**: >90% accuracy, >0.95 AUC score

### Feature Engineering
- Route length and complexity metrics
- Weather conditions and severity
- Battery margin calculations
- Airspace proximity analysis
- Terrain roughness assessment

### Model Training
```bash
# Generate synthetic training data
python ml/data/generate_synthetic_data.py

# Train advanced model with hyperparameter tuning
python ml/models/train_advanced_model.py

# Analyze model performance
jupyter notebook ml/notebooks/model_analysis.ipynb
```

## 🧪 Testing

### Run Simulations
```bash
# Run all sample mission simulations
python sim/run_simulation.py

# Run specific mission simulation
python sim/run_simulation.py "High-Risk Airport Proximity"
```

### Sample Missions
- **Safe Urban Delivery**: Low-risk short mission
- **High-Risk Airport Proximity**: Mission near restricted airspace
- **Long Range Survey**: Extended multi-waypoint mission
- **Emergency Response**: High-speed emergency scenario
- **Mountain Survey**: Challenging terrain mission

## 📈 Performance Metrics

### Model Performance
- **AUC Score**: 0.95+
- **Accuracy**: 90%+
- **Cross-Validation**: 5-fold CV with <2% variance
- **Feature Importance**: Top features identified and validated

### System Performance
- **API Response Time**: <200ms for mission planning
- **Simulation Speed**: Real-time playback capability
- **Frontend Load Time**: <3 seconds initial load
- **Memory Usage**: <500MB for full application

## 🔒 Security & Safety

### Data Protection
- No sensitive data stored in plaintext
- Secure API endpoints with validation
- Input sanitization and validation
- CORS protection enabled

### Safety Features
- No-fly zone detection and avoidance
- Battery safety margins
- Weather condition monitoring
- Risk threshold warnings

## 🛠️ Development

### Code Structure
- **Modular Architecture**: Separated concerns across services
- **Type Safety**: Pydantic models for API validation
- **Error Handling**: Comprehensive error handling and logging
- **Testing**: Unit tests and integration tests

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the backend
- **Code Documentation**: Inline docstrings and comments
- **User Guide**: This README and inline help text
- **Technical Specs**: Architecture diagrams and technical details

## 🚀 Deployment

### Production Setup
1. **Environment Variables**: Configure production settings
2. **Database**: Set up PostgreSQL for production
3. **Security**: Enable HTTPS and security headers
4. **Monitoring**: Set up logging and monitoring
5. **Scaling**: Configure load balancing if needed

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/uav_missions
REACT_APP_API_URL=http://localhost:8000
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- **OpenStreetMap** for map data
- **Leaflet** for interactive maps
- **XGBoost** for machine learning
- **FastAPI** for backend framework
- **React** for frontend framework

## 📞 Support

For questions, issues, or contributions:
- Create an issue in the repository
- Contact the development team
- Check the documentation and examples

---

**Built with ❤️ for safer UAV operations**
