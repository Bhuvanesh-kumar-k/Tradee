import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto_trading_app/providers/auth_provider.dart';
import 'package:crypto_trading_app/providers/settings_provider.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  // CoinDCX controllers
  final TextEditingController _coindcxApiKey = TextEditingController();
  final TextEditingController _coindcxApiSecret = TextEditingController();
  
  // Binance controllers
  final TextEditingController _binanceApiKey = TextEditingController();
  final TextEditingController _binanceApiSecret = TextEditingController();
  bool _binanceTestnet = true;
  
  // Margin controllers
  final TextEditingController _customMargin = TextEditingController();
  int? _scanInterval;
  
  // AI controllers
  String? _aiProvider;
  final TextEditingController _aiKey = TextEditingController();
  
  // Telegram controllers
  final TextEditingController _telegramApiId = TextEditingController();
  final TextEditingController _telegramApiHash = TextEditingController();
  final TextEditingController _telegramChannels = TextEditingController();
  
  // Trading settings
  bool _autoTradingEnabled = false;
  String _preferredCurrency = 'INR';
  List<String> _selectedTimeframes = ['1h', '4h', '8h', '1d'];
  final List<String> _availableTimeframes = ['1h', '2h', '4h', '8h', '1d'];
  double _riskPercentage = 0.25;
  
  // Secure storage for client-side keys
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    _loadSettings();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _coindcxApiKey.dispose();
    _coindcxApiSecret.dispose();
    _binanceApiKey.dispose();
    _binanceApiSecret.dispose();
    _customMargin.dispose();
    _aiKey.dispose();
    _telegramApiId.dispose();
    _telegramApiHash.dispose();
    _telegramChannels.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    await context.read<SettingsProvider>().fetchSettings();
    final settings = context.read<SettingsProvider>().settings;
    
    // Load keys from secure storage
    final coindcxKey = await _storage.read(key: 'coindcx_api_key');
    final coindcxSecret = await _storage.read(key: 'coindcx_api_secret');
    final binanceKey = await _storage.read(key: 'binance_api_key');
    final binanceSecret = await _storage.read(key: 'binance_api_secret');
    final binanceTestnet = await _storage.read(key: 'binance_testnet');
    final aiKey = await _storage.read(key: 'ai_api_key');
    final aiProvider = await _storage.read(key: 'ai_provider');
    final telegramApiId = await _storage.read(key: 'telegram_api_id');
    final telegramApiHash = await _storage.read(key: 'telegram_api_hash');
    
    // Populate controllers - use masked placeholders for existing keys
    if (coindcxKey != null && coindcxKey.isNotEmpty) {
      _coindcxApiKey.text = '••••••••••••••••';
    } else {
      _coindcxApiKey.text = '';
    }
    
    if (coindcxSecret != null && coindcxSecret.isNotEmpty) {
      _coindcxApiSecret.text = '••••••••••••••••';
    } else {
      _coindcxApiSecret.text = '';
    }
    
    if (binanceKey != null && binanceKey.isNotEmpty) {
      _binanceApiKey.text = '••••••••••••••••';
    } else {
      _binanceApiKey.text = '';
    }
    
    if (binanceSecret != null && binanceSecret.isNotEmpty) {
      _binanceApiSecret.text = '••••••••••••••••';
    } else {
      _binanceApiSecret.text = '';
    }
    
    _binanceTestnet = binanceTestnet == 'true';
    
    _customMargin.text = settings['custom_margin_allocation']?.toString() ?? '';
    _scanInterval = settings['scan_interval_minutes'] ?? 5;
    _aiProvider = aiProvider ?? settings['ai_provider'] ?? 'None';
    
    if (aiKey != null && aiKey.isNotEmpty) {
      _aiKey.text = '••••••••••••••••';
    } else {
      _aiKey.text = '';
    }
    
    _telegramApiId.text = telegramApiId ?? '';
    _telegramApiHash.text = telegramApiHash ?? '';
    _telegramChannels.text = settings['telegram_channels']?.join(', ') ?? '';
    
    // Trading settings
    _autoTradingEnabled = settings['auto_trading_enabled'] ?? false;
    _preferredCurrency = settings['preferred_currency'] ?? 'INR';
    _selectedTimeframes = List<String>.from(settings['trading_timeframes'] ?? ['1h', '4h', '8h', '1d']);
  }

  @override
  Widget build(BuildContext context) {
    final settingsProvider = context.watch<SettingsProvider>();
    final authProvider = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => _showAboutEngine(),
            tooltip: 'About Strategy & Engine',
          ),
        ],
      ),
      body: Column(
        children: [
          // User Info Card
          _buildUserInfoCard(authProvider.user),
          SizedBox(height: 16.h),
          
          // Tab Bar
          TabBar(
            controller: _tabController,
            isScrollable: true,
            tabs: const [
              Tab(text: 'CoinDCX'),
              Tab(text: 'Binance'),
              Tab(text: 'Margin'),
              Tab(text: 'AI'),
              Tab(text: 'Telegram'),
              Tab(text: 'Trading'),
            ],
          ),
          
          // Tab Content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildCoinDCXTab(settingsProvider),
                _buildBinanceTab(),
                _buildMarginTab(settingsProvider),
                _buildAITab(settingsProvider),
                _buildTelegramTab(settingsProvider),
                _buildTradingTab(settingsProvider),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserInfoCard(Map<String, dynamic>? user) {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16.w),
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryColor.withValues(alpha: 0.2),
            AppTheme.secondaryColor.withValues(alpha: 0.2),
          ],
        ),
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 32.r,
            backgroundColor: AppTheme.primaryColor,
            child: Icon(Icons.person, size: 32.sp, color: AppTheme.backgroundColor),
          ),
          SizedBox(width: 16.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  user?['name'] ?? 'User',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                SizedBox(height: 4.h),
                Text(
                  user?['email'] ?? '',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (user?['experience_level'] != null)
                  Container(
                    margin: EdgeInsets.only(top: 4.h),
                    padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
                    decoration: BoxDecoration(
                      color: AppTheme.cardColor,
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                    child: Text(
                      user!['experience_level'],
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCoinDCXTab(SettingsProvider provider) {
    final settings = provider.settings;
    
    return ListView(
      padding: EdgeInsets.all(16.w),
      children: [
        Text(
          'CoinDCX API Credentials',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        SizedBox(height: 16.h),
        _buildHelpText(
          'Get your API credentials from CoinDCX dashboard under Settings > API Keys. '
          'Enable futures trading permissions for full functionality.',
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _coindcxApiKey,
          decoration: InputDecoration(
            labelText: 'API Key',
            prefixIcon: const Icon(Icons.key_outlined),
            suffixIcon: _buildHelpTooltip(
              'Your CoinDCX API Key. Found in your CoinDCX account Settings > API Keys section.',
            ),
          ),
          obscureText: true,
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _coindcxApiSecret,
          decoration: InputDecoration(
            labelText: 'API Secret',
            prefixIcon: const Icon(Icons.vpn_key_outlined),
            suffixIcon: _buildHelpTooltip(
              'Your CoinDCX API Secret. Keep this confidential and never share it.',
            ),
          ),
          obscureText: true,
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: () => _saveCoinDCXSettings(),
          child: const Text('Save Credentials'),
        ),
        SizedBox(height: 8.h),
        if (settings['has_coindcx_keys'] == true)
          Container(
            padding: EdgeInsets.all(12.w),
            decoration: BoxDecoration(
              color: AppTheme.successColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle, color: AppTheme.successColor, size: 20.sp),
                SizedBox(width: 8.w),
                Text(
                  'Credentials configured',
                  style: TextStyle(color: AppTheme.successColor),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildBinanceTab() {
    return ListView(
      padding: EdgeInsets.all(16.w),
      children: [
        Text(
          'Binance Futures API Credentials',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        SizedBox(height: 16.h),
        _buildHelpText(
          'Get your API credentials from Binance dashboard under API Management. '
          'Enable futures trading permissions for full functionality.',
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _binanceApiKey,
          decoration: InputDecoration(
            labelText: 'API Key',
            prefixIcon: const Icon(Icons.key_outlined),
            suffixIcon: _buildHelpTooltip(
              'Your Binance API Key. Found in your Binance account API Management section.',
            ),
          ),
          obscureText: true,
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _binanceApiSecret,
          decoration: InputDecoration(
            labelText: 'API Secret',
            prefixIcon: const Icon(Icons.vpn_key_outlined),
            suffixIcon: _buildHelpTooltip(
              'Your Binance API Secret. Keep this confidential and never share it.',
            ),
          ),
          obscureText: true,
        ),
        SizedBox(height: 16.h),
        SwitchListTile(
          title: const Text('Use Futures Testnet (Sandbox)'),
          subtitle: const Text('Trade with fake USDT before risking real capital'),
          value: _binanceTestnet,
          onChanged: (value) {
            setState(() {
              _binanceTestnet = value;
            });
          },
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: () => _saveBinanceSettings(),
          child: const Text('Save Credentials'),
        ),
        SizedBox(height: 8.h),
        Container(
          padding: EdgeInsets.all(12.w),
          decoration: BoxDecoration(
            color: AppTheme.warningColor.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8.r),
            border: Border.all(color: AppTheme.warningColor.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              Icon(Icons.info_outline, color: AppTheme.warningColor, size: 20.sp),
              SizedBox(width: 8.w),
              Expanded(
                child: Text(
                  'Keys are stored locally on your device. Never share them with anyone.',
                  style: TextStyle(color: AppTheme.warningColor, fontSize: 12.sp),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _saveBinanceSettings() async {
    await _storage.write(key: 'binance_api_key', value: _binanceApiKey.text.trim());
    await _storage.write(key: 'binance_api_secret', value: _binanceApiSecret.text.trim());
    await _storage.write(key: 'binance_testnet', value: _binanceTestnet.toString());
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Binance credentials saved securely on device')),
      );
    }
  }

  Widget _buildMarginTab(SettingsProvider provider) {
    return ListView(
      padding: EdgeInsets.all(16.w),
      children: [
        Text(
          'Margin Settings',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        SizedBox(height: 16.h),
        _buildHelpText(
          'Configure your risk per trade. Leave empty to auto-allocate 20-25% of your CoinDCX futures balance.',
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _customMargin,
          decoration: InputDecoration(
            labelText: 'Custom Margin Allocation (USDT)',
            prefixIcon: const Icon(Icons.account_balance_wallet_outlined),
            hintText: 'Leave empty to use risk percentage below',
            suffixIcon: _buildHelpTooltip(
              'Fixed USDT amount to use per trade. If empty, system uses your risk percentage of balance.',
            ),
          ),
          keyboardType: TextInputType.number,
        ),
        SizedBox(height: 24.h),
        Text(
          'Risk Per Trade: ${(_riskPercentage * 100).toInt()}% of Balance',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        SizedBox(height: 8.h),
        Slider(
          value: _riskPercentage,
          min: 0.03,
          max: 0.50,
          divisions: 47,
          label: '${(_riskPercentage * 100).toInt()}%',
          activeColor: AppTheme.primaryColor,
          onChanged: (val) {
            setState(() {
              _riskPercentage = val;
            });
          },
        ),
        SizedBox(height: 8.h),
        Text(
          'Recommended: 15% - 25% for balanced portfolio protection.',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.textSecondary),
        ),
        SizedBox(height: 16.h),
        Text(
          'Scan Interval',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        SizedBox(height: 8.h),
        DropdownButtonFormField<int>(
          value: _scanInterval,
          decoration: InputDecoration(
            prefixIcon: const Icon(Icons.schedule),
            suffixIcon: _buildHelpTooltip(
              'How often the market scanner runs. Shorter intervals = more signals but higher API usage.',
            ),
          ),
          items: const [
            DropdownMenuItem(value: 3, child: Text('3 minutes')),
            DropdownMenuItem(value: 5, child: Text('5 minutes')),
            DropdownMenuItem(value: 7, child: Text('7 minutes')),
            DropdownMenuItem(value: 10, child: Text('10 minutes')),
            DropdownMenuItem(value: 15, child: Text('15 minutes')),
            DropdownMenuItem(value: 30, child: Text('30 minutes')),
          ],
          onChanged: (value) {
            setState(() {
              _scanInterval = value;
            });
          },
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: () => _saveMarginSettings(),
          child: const Text('Save Settings'),
        ),
      ],
    );
  }

  Widget _buildAITab(SettingsProvider provider) {
    final settings = provider.settings;
    
    return ListView(
      padding: EdgeInsets.all(16.w),
      children: [
        Text(
          'AI Configuration',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        SizedBox(height: 16.h),
        _buildHelpText(
          'AI validates Telegram trading signals. Gemini is recommended (free tier, no credit card required).',
        ),
        SizedBox(height: 16.h),
        DropdownButtonFormField<String>(
          value: _aiProvider,
          decoration: InputDecoration(
            labelText: 'AI Provider',
            prefixIcon: const Icon(Icons.psychology_outlined),
            suffixIcon: _buildHelpTooltip(
              'Gemini (recommended): Free tier, no credit card. OpenAI: Paid, requires API key.',
            ),
          ),
          items: const [
            DropdownMenuItem(value: 'None', child: Text('None')),
            DropdownMenuItem(value: 'Gemini', child: Text('Google Gemini (Recommended)')),
            DropdownMenuItem(value: 'Copilot', child: Text('Microsoft Copilot')),
            DropdownMenuItem(value: 'OpenAI', child: Text('OpenAI GPT')),
          ],
          onChanged: (value) {
            setState(() {
              _aiProvider = value;
            });
          },
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _aiKey,
          decoration: InputDecoration(
            labelText: 'API Key',
            prefixIcon: const Icon(Icons.key_outlined),
            suffixIcon: _buildHelpTooltip(
              'Your AI provider API key. Get one from: Gemini (makersuite.google.com) or OpenAI (platform.openai.com)',
            ),
          ),
          obscureText: true,
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: () => _verifyAndSaveAIKey(),
          child: const Text('Verify & Save Key'),
        ),
        SizedBox(height: 8.h),
        if (settings['ai_enabled'] == true)
          Container(
            padding: EdgeInsets.all(12.w),
            decoration: BoxDecoration(
              color: AppTheme.successColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle, color: AppTheme.successColor, size: 20.sp),
                SizedBox(width: 8.w),
                Text(
                  'AI enabled: ${settings['ai_provider']}',
                  style: TextStyle(color: AppTheme.successColor),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildTelegramTab(SettingsProvider provider) {
    final settings = provider.settings;
    
    return ListView(
      padding: EdgeInsets.all(16.w),
      children: [
        Text(
          'Telegram Configuration',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        SizedBox(height: 16.h),
        _buildHelpText(
          'Connect to Telegram signal channels. Get API credentials from my.telegram.org/apps.',
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _telegramApiId,
          decoration: InputDecoration(
            labelText: 'API ID',
            prefixIcon: const Icon(Icons.tag),
            suffixIcon: _buildHelpTooltip(
              'Your Telegram API ID (numeric). Get it from my.telegram.org/apps',
              serviceType: 'telegram',
            ),
          ),
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _telegramApiHash,
          decoration: InputDecoration(
            labelText: 'API Hash',
            prefixIcon: const Icon(Icons.fingerprint),
            suffixIcon: _buildHelpTooltip(
              'Your Telegram API Hash (string). Get it from my.telegram.org/apps',
            ),
          ),
          obscureText: true,
        ),
        SizedBox(height: 16.h),
        TextFormField(
          controller: _telegramChannels,
          decoration: InputDecoration(
            labelText: 'Channels (comma separated)',
            prefixIcon: const Icon(Icons.tag),
            hintText: '@channel1, @channel2',
            suffixIcon: _buildHelpTooltip(
              'Telegram channels to monitor for signals. Use @username format or channel ID.',
              serviceType: 'telegram',
            ),
          ),
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: () => _saveTelegramSettings(),
          child: const Text('Save Settings'),
        ),
        SizedBox(height: 8.h),
        if (settings['has_credentials'] == true)
          Container(
            padding: EdgeInsets.all(12.w),
            decoration: BoxDecoration(
              color: AppTheme.successColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle, color: AppTheme.successColor, size: 20.sp),
                SizedBox(width: 8.w),
                Text(
                  'Telegram configured',
                  style: TextStyle(color: AppTheme.successColor),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildTradingTab(SettingsProvider provider) {
    return ListView(
      padding: EdgeInsets.all(16.w),
      children: [
        Text(
          'Trading Settings',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        SizedBox(height: 16.h),
        _buildHelpText(
          'Configure automated trading behavior, preferred currency, and execution timeframes.',
        ),
        SizedBox(height: 16.h),
        
        // Auto-Trading Toggle
        SwitchListTile(
          title: const Text('Auto-Trading Enabled'),
          subtitle: const Text('Allow system to automatically execute trades'),
          value: _autoTradingEnabled,
          onChanged: (value) {
            setState(() {
              _autoTradingEnabled = value;
            });
          },
          activeThumbColor: AppTheme.primaryColor,
        ),
        SizedBox(height: 16.h),
        
        // Currency Selector
        Text(
          'Preferred Currency',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        SizedBox(height: 8.h),
        DropdownButtonFormField<String>(
          initialValue: _preferredCurrency,
          decoration: InputDecoration(
            prefixIcon: const Icon(Icons.currency_exchange),
            suffixIcon: _buildHelpTooltip(
              'Choose your preferred currency for trading calculations. INR will be converted to USDT at current rates.',
            ),
          ),
          items: const [
            DropdownMenuItem(value: 'INR', child: Text('INR (Indian Rupee)')),
            DropdownMenuItem(value: 'USDT', child: Text('USDT (Tether)')),
          ],
          onChanged: (value) {
            setState(() {
              _preferredCurrency = value ?? 'INR';
            });
          },
        ),
        SizedBox(height: 16.h),
        
        // Timeframe Selection
        Text(
          'Execution Timeframes ("Take Trade In")',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        SizedBox(height: 8.h),
        _buildHelpText(
          'Select which timeframes the scanner should use for trade execution. At least one timeframe must be selected.',
        ),
        SizedBox(height: 8.h),
        Wrap(
          spacing: 8.w,
          runSpacing: 8.h,
          children: _availableTimeframes.map((timeframe) {
            final isSelected = _selectedTimeframes.contains(timeframe);
            return FilterChip(
              label: Text(timeframe),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedTimeframes.add(timeframe);
                  } else {
                    _selectedTimeframes.remove(timeframe);
                  }
                });
              },
              selectedColor: AppTheme.primaryColor.withValues(alpha: 0.3),
              checkmarkColor: AppTheme.primaryColor,
            );
          }).toList(),
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: () => _saveTradingSettings(),
          child: const Text('Save Trading Settings'),
        ),
      ],
    );
  }

  Widget _buildHelpText(String text) {
    return Container(
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, color: AppTheme.primaryColor, size: 20.sp),
          SizedBox(width: 8.w),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHelpTooltip(String message, {String? serviceType}) {
    return IconButton(
      icon: Icon(Icons.help_outline, color: AppTheme.textSecondary, size: 20.sp),
      onPressed: () async {
        if (serviceType != null) {
          await _showDynamicKeyGuide(serviceType);
        } else {
          _showStaticHelp(message);
        }
      },
    );
  }

  void _showStaticHelp(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.cardColor,
        title: Row(
          children: [
            Icon(Icons.info_outline, color: AppTheme.primaryColor),
            SizedBox(width: 8.w),
            const Text('Help'),
          ],
        ),
        content: Text(
          message,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  Future<void> _showDynamicKeyGuide(String serviceType) async {
    try {
      final response = await ApiClient.get(Constants.keyGuides);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final guides = data['guides'] as Map<String, dynamic>?;
        final guideText = guides?[serviceType] ?? 'Guide not available';
        
        if (mounted) {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              backgroundColor: AppTheme.cardColor,
              title: Row(
                children: [
                  Icon(Icons.info_outline, color: AppTheme.primaryColor),
                  SizedBox(width: 8.w),
                  Text('${serviceType.toUpperCase()} Setup Guide'),
                ],
              ),
              content: SingleChildScrollView(
                child: Text(
                  guideText,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Got it'),
                ),
              ],
            ),
          );
        }
      } else {
        _showStaticHelp('Unable to fetch guide. Please check your connection.');
      }
    } catch (e) {
      _showStaticHelp('Error loading guide: $e');
    }
  }

  Future<void> _saveCoinDCXSettings() async {
    // Save directly to secure storage
    await _storage.write(key: 'coindcx_api_key', value: _coindcxApiKey.text);
    await _storage.write(key: 'coindcx_api_secret', value: _coindcxApiSecret.text);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('CoinDCX credentials saved securely on your device')),
      );
    }
  }

  Future<void> _saveMarginSettings() async {
    final provider = context.read<SettingsProvider>();
    final success = await provider.updateSettings({
      'margin': {
        'custom_margin_allocation': _customMargin.text.isEmpty ? null : double.tryParse(_customMargin.text),
        'risk_percentage_per_trade': _riskPercentage,
        'scan_interval_minutes': _scanInterval,
      }
    });
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Margin settings saved')),
      );
    }
  }

  Future<void> _verifyAndSaveAIKey() async {
    if (_aiProvider == null || _aiProvider == 'None') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select an AI provider')),
      );
      return;
    }
    if (_aiKey.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter an API key')),
      );
      return;
    }
    
    // Save to secure storage
    await _storage.write(key: 'ai_api_key', value: _aiKey.text);
    await _storage.write(key: 'ai_provider', value: _aiProvider!);
    
    // Verify with backend (key not stored there)
    final provider = context.read<SettingsProvider>();
    final success = await provider.verifyAiKey(_aiProvider!, _aiKey.text);
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('AI key verified and saved securely on your device')),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Verification failed: ${provider.errorMessage}')),
      );
    }
  }

  Future<void> _saveTelegramSettings() async {
    // Save credentials to secure storage
    await _storage.write(key: 'telegram_api_id', value: _telegramApiId.text);
    await _storage.write(key: 'telegram_api_hash', value: _telegramApiHash.text);
    
    // Save channels to backend (non-sensitive data)
    final channelsList = _telegramChannels.text
        .split(',')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();
    
    final provider = context.read<SettingsProvider>();
    final success = await provider.updateSettings({
      'telegram': {
        'channels': channelsList,
      }
    });
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Telegram settings saved securely on your device')),
      );
    }
  }

  Future<void> _showAboutEngine() async {
    try {
      final response = await ApiClient.get(Constants.about);
      String aboutContent = '';
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        aboutContent = data['about'] ?? _getDefaultAboutContent();
      } else {
        aboutContent = _getDefaultAboutContent();
      }
      
      if (mounted) {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: AppTheme.cardColor,
          builder: (context) => DraggableScrollableSheet(
            initialChildSize: 0.7,
            minChildSize: 0.5,
            maxChildSize: 0.95,
            expand: false,
            builder: (context, scrollController) => Container(
              padding: EdgeInsets.all(20.w),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.engineering, color: AppTheme.primaryColor, size: 28.sp),
                      SizedBox(width: 12.w),
                      Text(
                        'About Strategy & Engine',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                    ],
                  ),
                  SizedBox(height: 20.h),
                  Expanded(
                    child: SingleChildScrollView(
                      controller: scrollController,
                      child: Text(
                        aboutContent,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                  ),
                  SizedBox(height: 16.h),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Close'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading info: $e')),
        );
      }
    }
  }

  String _getDefaultAboutContent() {
    return '''
ENGINE CAPABILITIES
==================

• 24/7 Automated Market Scanning
  - Multi-timeframe analysis (1h, 4h, 8h, 1d)
  - Real-time indicator calculations
  - BTC Macro Trend filtering

• News Circuit Breakers
  - Economic calendar integration
  - Automatic trading freeze during high-impact events
  - Volatility-based position sizing

• Risk Management
  - ATR-based Trailing Stops
  - Dynamic position sizing (20-25% of balance)
  - Multi-timeframe confluence validation

ANALYTICAL RULES
================

BTC Macro 1D Regime
- EMA 20/50/200 trend alignment
- MACD momentum confirmation
- Volume SMA support validation

Entry Conditions
- ADX Choppiness >= 20 (trending market)
- EMA Golden Cross / Death Cross
- RSI divergence detection
- Dynamic swing level breaks

Exit Conditions
- ATR Trailing Stop (2x ATR)
- Take Profit at key resistance
- Stop Loss below recent swing low

INDICATORS USED
===============

• EMA (20, 50, 200) - Trend direction
• MACD - Momentum confirmation
• RSI (14) - Overbought/Oversold
• ADX (14) - Trend strength
• ATR (14) - Volatility measurement
• Volume SMA - Volume confirmation
    ''';
  }

  Future<void> _saveTradingSettings() async {
    if (_selectedTimeframes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one timeframe')),
      );
      return;
    }
    
    final provider = context.read<SettingsProvider>();
    final success = await provider.updateSettings({
      'trading': {
        'auto_trading_enabled': _autoTradingEnabled,
        'preferred_currency': _preferredCurrency,
        'trading_timeframes': _selectedTimeframes,
      }
    });
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Trading settings saved')),
      );
    }
  }
}
