# CivicSaathi - React Native Expo Project

## Project Overview
A citizen grievance mobile app for Nagar Nigam Jaipur municipality. Citizens can report complaints (potholes, garbage, streetlights), track status, and rate public facilities.

## Tech Stack
- React Native with Expo (managed workflow)
- TypeScript
- React Navigation v6
- Axios for API calls
- AsyncStorage for token persistence
- Expo Location, Image Picker, Maps

## Color Palette (Anime-inspired, eye-pleasant)
- Primary: `#FF6B6B` (Soft Coral Red)
- Secondary: `#FFE5E5` (Light Blush Pink)
- Accent: `#FF8E8E` (Pastel Red)
- Background: `#FFF5F5` (Cream White)
- Card: `#FFFFFF`
- Text Primary: `#2D2D2D`
- Text Secondary: `#666666`
- Success: `#4CAF50`
- Warning: `#FFB74D`
- Error: `#F44336`

## Folder Structure
```
CivicSaathi/
├── src/
│   ├── components/
│   ├── screens/
│   │   ├── auth/
│   │   └── main/
│   ├── navigation/
│   ├── services/
│   ├── context/
│   ├── theme/
│   ├── types/
│   └── utils/
├── assets/
├── App.tsx
└── app.json
```

## API Endpoints (Backend: Django REST)
```
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/profile/
PUT  /api/auth/profile/
POST /api/auth/change-password/
POST /api/auth/forgot-password/
POST /api/auth/verify-otp/
POST /api/auth/reset-password/

GET  /api/complaints/
POST /api/complaints/create/
GET  /api/complaints/<id>/
GET  /api/complaints/<id>/logs/

GET  /api/categories/
GET  /api/departments/

GET  /api/facilities/
GET  /api/facilities/nearby/
GET  /api/facilities/<id>/
POST /api/facilities/<id>/rate/
```

## Features to Implement
1. **Authentication Flow**: Login, Register, Forgot Password with OTP
2. **Dashboard**: Quick stats, recent complaints
3. **Complaint Management**: Create, list, detail, track timeline
4. **Facilities**: List, map view, rate facilities
5. **Profile**: View/edit profile, change password

## Development Commands
```bash
# Start development server
npx expo start

# Run on Android
npx expo start --android

# Run on iOS
npx expo start --ios
```
