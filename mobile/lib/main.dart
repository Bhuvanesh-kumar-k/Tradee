import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/auth_provider.dart';
import 'package:crypto_trading_app/providers/trade_provider.dart';
import 'package:crypto_trading_app/providers/scanner_provider.dart';
import 'package:crypto_trading_app/providers/settings_provider.dart';
import 'package:crypto_trading_app/services/websocket_service.dart';
import 'package:crypto_trading_app/screens/auth/login_screen.dart';
import 'package:crypto_trading_app/screens/home/main_screen.dart';
import 'package:crypto_trading_app/screens/legal/terms_dialog.dart';
import 'package:crypto_trading_app/utils/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => TradeProvider()),
        ChangeNotifierProvider(create: (_) => ScannerProvider()),
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
        ChangeNotifierProvider(create: (_) => WebSocketService()),
      ],
      child: ScreenUtilInit(
        designSize: const Size(375, 812),
        minTextAdapt: true,
        splitScreenMode: true,
        builder: (context, child) {
          return MaterialApp(
            title: 'Tradee',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.darkTheme,
            home: const AuthWrapper(),
          );
        },
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    if (!authProvider.isAuthenticated) {
      return const LoginScreen();
    }

    if (!authProvider.termsAccepted) {
      return const TermsAgreementScreen();
    }

    return const MainScreen();
  }
}
