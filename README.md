# 🌱 AgriMind – AI-Powered Agriculture Assistant

AgriMind is an AI-powered agriculture decision-support platform designed to help farmers make informed farming decisions using soil health data and weather information.

Farmers can enter soil parameters or upload a Soil Health Card report to analyze soil conditions, explore suitable crops, and receive fertilizer recommendations. The platform also provides weather-based farming advisories and multilingual assistance in English, Hindi, and Marathi.

The goal of AgriMind is to make agricultural information easier to understand and help farmers make better decisions about their crops, soil, and fertilizer usage.

## ✨ Key Features

- **Soil Health Analysis:** Enter soil parameters manually or upload a soil report for analysis.
- **Crop Recommendations:** Get suitable crop suggestions based on soil conditions and nutrient levels.
- **Fertilizer Recommendations:** Receive guidance on fertilizers and soil amendments based on soil requirements.
- **Weather-Based Advisories:** Access weather information and alerts to help plan farming activities.
- **AI Assistant:** Get agricultural information and explanations through retrieval-based responses and AI integrations.
- **Multilingual Support:** Interact in English, Hindi, and Marathi, with voice input and speech output.
- **PDF Report Parsing:** Extract soil information from supported Soil Health Card report formats.
- **User Authentication:** Create an account, log in securely, and save soil analysis reports.
- **Responsive Interface:** Use the platform across desktop and mobile devices.
- **Organic Farming Option:** Enable organic-only recommendations when using the recommendation system.

## 🛠️ Tech Stack

**Frontend**
- React.js
- Vite
- CSS

**Backend**
- Python
- FastAPI
- Pydantic

**Database and Authentication**
- SQLite
- SQLAlchemy
- JWT authentication
- bcrypt password hashing

**AI and External Services**
- OpenRouter
- Google Gemini
- Open-Meteo
- WeatherAPI

**Document Processing**
- PDF text extraction
- Rule-based soil report parsing

## ⚙️ How It Works

1. The user enters soil parameters or uploads a soil health report.
2. AgriMind extracts and analyzes the available soil information.
3. The system evaluates soil nutrients and other relevant conditions.
4. It generates crop suggestions and fertilizer or soil amendment guidance.
5. Weather information is used to provide relevant farming advisories.
6. The user can explore the results through the interface and save reports for future reference.

## 🎯 Project Goals

- Make soil health information easier for farmers to understand.
- Support crop selection using soil-related data.
- Provide more informed fertilizer and soil amendment guidance.
- Help farmers consider weather conditions when planning activities.
- Improve access to agricultural information through multilingual interaction.

## 🚀 Deployment

AgriMind uses a separate frontend and backend architecture.

- **Frontend:** React application deployed on Vercel.
- **Backend:** FastAPI application deployed on Render.
- **Database:** SQLite with SQLAlchemy for data management.

## 🔮 Future Scope

- Improve soil report parsing for different report formats.
- Expand crop recommendations with region-specific agricultural data.
- Validate recommendation rules with agricultural experts and field data.
- Improve multilingual support and the accuracy of AI-generated explanations.
- Add more comprehensive testing and monitoring for deployed services.

## ⚠️ Disclaimer

AgriMind is an agricultural decision-support tool. Its recommendations should be treated as guidance and verified against local agricultural practices and expert advice before making important farming decisions.

## 👨‍💻 About

AgriMind is a project exploring how AI, soil analysis, and weather data can be combined to make agricultural decision support more accessible and practical.
