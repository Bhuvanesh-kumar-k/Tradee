import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/auth_provider.dart';
import 'package:crypto_trading_app/screens/home/tabs/dashboard_tab.dart';
import 'package:crypto_trading_app/screens/home/tabs/scanner_tab.dart';
import 'package:crypto_trading_app/screens/home/tabs/single_coin_tab.dart';
import 'package:crypto_trading_app/screens/home/tabs/telegram_tab.dart';
import 'package:crypto_trading_app/screens/settings/settings_screen.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  final List<Widget> _tabs = [
    const DashboardTab(),
    const ScannerTab(),
    const SingleCoinTab(),
    const TelegramTab(),
  ];

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Crypto Trading'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SettingsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await authProvider.logout();
            },
          ),
        ],
      ),
      body: _tabs[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard_outlined),
            activeIcon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.radar_outlined),
            activeIcon: Icon(Icons.radar),
            label: 'Scanner',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.search_outlined),
            activeIcon: Icon(Icons.search),
            label: 'Check Coin',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.telegram_outlined),
            activeIcon: Icon(Icons.telegram),
            label: 'Signals',
          ),
        ],
      ),
    );
  }
}
