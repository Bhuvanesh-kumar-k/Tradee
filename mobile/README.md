# Crypto Trading Platform - Mobile App

Flutter mobile application for the crypto futures trading platform with 4-tab navigation.

## Features

- **Authentication**: Email OTP registration and login
- **Dashboard**: Account balance, trade statistics, active positions
- **Live Scanner**: Real-time market scanning logs with indicator values
- **Single Coin Check**: On-demand analysis for any cryptocurrency
- **Telegram Signals**: AI-validated trading signal feed
- **Settings**: Configure CoinDCX keys, margin, AI, and Telegram credentials

## Prerequisites

- Flutter SDK 3.0+
- Android Studio / Xcode
- Android 5.0+ / iOS 12.0+

## Installation

1. Navigate to mobile directory:
```bash
cd mobile
```

2. Install dependencies:
```bash
flutter pub get
```

3. Configure API URL:
Edit `lib/utils/constants.dart` and update `apiBaseUrl` to your backend server address.

## Running the App

### Android
```bash
flutter run
```

### iOS
```bash
flutter run
```

### Build APK
```bash
flutter build apk --release
```

### Build iOS
```bash
flutter build ios --release
```

## App Structure

```
lib/
├── main.dart                 # App entry point
├── utils/
│   ├── theme.dart           # Dark theme configuration
│   ├── constants.dart       # API endpoints and constants
│   └── api_client.dart      # HTTP client wrapper
├── providers/
│   ├── auth_provider.dart   # Authentication state management
│   ├── trade_provider.dart  # Trade data state management
│   ├── scanner_provider.dart # Scanner state management
│   └── settings_provider.dart # Settings state management
├── screens/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   └── otp_screen.dart
│   ├── home/
│   │   ├── main_screen.dart
│   │   └── tabs/
│   │       ├── dashboard_tab.dart
│   │       ├── scanner_tab.dart
│   │       ├── single_coin_tab.dart
│   │       └── telegram_tab.dart
│   └── settings/
│       └── settings_screen.dart
```

## Configuration

### Backend API URL
Update in `lib/utils/constants.dart`:
```dart
static const String apiBaseUrl = 'http://YOUR_BACKEND_URL:8000/api/v1';
```

### WebSocket URL
Update in `lib/utils/constants.dart`:
```dart
static const String wsUrl = 'ws://YOUR_BACKEND_URL:8000/api/v1/ws/live-updates';
```

## Screens

### 1. Authentication
- **Login Screen**: Email/password login
- **OTP Screen**: Email verification with 6-digit OTP

### 2. Dashboard (Tab 1)
- Account balance display
- Trade statistics (Total, Win Rate, Net PnL)
- Period selector (Today, Yesterday, Week, Month)
- Active positions with live PnL
- Emergency close button

### 3. Live Scanner (Tab 2)
- Scanner status (Active/Frozen)
- News circuit breaker alerts
- Real-time scanner logs
- Indicator values (RSI, ADX, MACD)
- Trend and signal badges

### 4. Single Coin Check (Tab 3)
- Coin symbol search
- Multi-timeframe analysis
- Trade setup recommendations
- Entry, TP, SL, leverage

### 5. Telegram Signals (Tab 4)
- Signal listener status
- Parsed signal cards
- AI verdict and confidence
- Channel and timestamp

### 6. Settings
- **CoinDCX Tab**: API key and secret
- **Margin Tab**: Custom allocation, scan interval
- **AI Tab**: Provider selection, API key verification
- **Telegram Tab**: API credentials, channel list

## Theme

Dark financial theme with:
- Primary: #00D4AA (Green)
- Secondary: #7C3AED (Purple)
- Background: #0D1117 (Dark)
- Card: #161B22
- Success: #3FB950
- Danger: #DA3633
- Warning: #D29922

## Dependencies

- `flutter_screenutil`: Responsive design
- `provider`: State management
- `http`: HTTP requests
- `web_socket_channel`: WebSocket client
- `flutter_secure_storage`: Secure token storage
- `fl_chart`: Charts and graphs

## Security

- JWT tokens stored securely using flutter_secure_storage
- All API calls use Bearer token authentication
- Sensitive fields (API keys) obscured in UI

## License

Proprietary - All rights reserved
