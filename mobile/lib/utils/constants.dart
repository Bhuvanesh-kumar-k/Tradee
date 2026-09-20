class Constants {
  static const String apiBaseUrl = 'https://tradee-backend.onrender.com/api/v1';
  static const String wsUrl = 'wss://tradee-backend.onrender.com/api/v1/ws/live-updates';

  // System endpoints (relative paths)
  static const String terms = '/system/terms';
  static const String acceptTerms = '/system/accept-terms';
  static const String about = '/system/about';
  static const String keyGuides = '/system/key-guides';
  static const String conversionRate = '/system/conversion-rate';

  // Auth & Trading endpoints (relative paths)
  static const String requestOtp = '/auth/request-otp';
  static const String verifyOtp = '/auth/verify-otp';
  static const String login = '/auth/login';
  static const String settings = '/settings/me';
  static const String verifyAiKey = '/settings/verify-ai-key';
  static const String scannerStatus = '/scanner/status';
  static const String checkCoin = '/scanner/check-coin';
  static const String scanAll = '/scanner/scan-all';
  static const String scannerLogs = '/scanner/logs';
  static const String balance = '/scanner/balance';
  static const String activeTrades = '/trades/active';
  static const String tradeHistory = '/trades/history';
  static const String tradeStats = '/trades/stats';
  static const String closeTrade = '/trades/close';
  static const String telegramStatus = '/telegram/status';
  static const String telegramSignals = '/telegram/signals';
  static const String startTelegram = '/telegram/start';
  static const String stopTelegram = '/telegram/stop';
}