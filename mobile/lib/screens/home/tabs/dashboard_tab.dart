import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto_trading_app/providers/trade_provider.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class DashboardTab extends StatefulWidget {
  const DashboardTab({super.key});

  @override
  State<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends State<DashboardTab> {
  String _selectedPeriod = 'today';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  double _accountBalance = 0.0;
  double _marginInUse = 0.0;
  bool _hasCoinDCXKeys = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final tradeProvider = context.read<TradeProvider>();
    
    // Check if CoinDCX keys exist
    final apiKey = await _storage.read(key: 'coindcx_api_key');
    final apiSecret = await _storage.read(key: 'coindcx_api_secret');
    _hasCoinDCXKeys = apiKey != null && apiSecret != null;
    
    if (_hasCoinDCXKeys) {
      // Fetch live balance from API
      try {
        final response = await ApiClient.get(Constants.balance);
        if (response.statusCode == 200) {
          final data = Map<String, dynamic>.from(
            // Parse JSON response
            // Assuming API returns { "balance": 1234.56, "margin_in_use": 234.56 }
            // Adjust based on actual API response structure
            {}
          );
          _accountBalance = (data['balance'] ?? 0.0) as double;
          _marginInUse = (data['margin_in_use'] ?? 0.0) as double;
        }
      } catch (_) {
        // On error, keep zeros
      }
    }
    
    await Future.wait([
      tradeProvider.fetchActiveTrades(),
      tradeProvider.fetchTradeStats(_selectedPeriod),
    ]);
    
    if (mounted) {
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    final tradeProvider = context.watch<TradeProvider>();

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Balance Card
            _buildBalanceCard(),
            SizedBox(height: 16.h),
            
            // Stats Cards
            _buildStatsCards(tradeProvider.stats),
            SizedBox(height: 16.h),
            
            // Period Selector
            _buildPeriodSelector(),
            SizedBox(height: 16.h),
            
            // Active Positions
            Text(
              'Active Positions',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 12.h),
            tradeProvider.activeTrades.isEmpty
                ? _buildEmptyState('No active positions')
                : ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: tradeProvider.activeTrades.length,
                    itemBuilder: (context, index) {
                      return _buildPositionCard(tradeProvider.activeTrades[index]);
                    },
                  ),
          ],
        ),
      ),
    );
  }

  Widget _buildBalanceCard() {
    return Container(
      padding: EdgeInsets.all(20.w),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryColor.withValues(alpha: 0.2),
            AppTheme.secondaryColor.withValues(alpha: 0.2),
          ],
        ),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Account Balance',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (!_hasCoinDCXKeys)
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                  decoration: BoxDecoration(
                    color: AppTheme.warningColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Text(
                    'CoinDCX Disconnected (Connect in Settings)',
                    style: TextStyle(
                      color: AppTheme.warningColor,
                      fontSize: 10.sp,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          SizedBox(height: 8.h),
          Text(
            '\$${_accountBalance.toStringAsFixed(2)} USDT',
            style: Theme.of(context).textTheme.displayMedium,
          ),
          SizedBox(height: 8.h),
          Text(
            'Margin in Use: \$${_marginInUse.toStringAsFixed(2)} USDT',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCards(TradeStats? stats) {
    if (stats == null) {
      return const SizedBox.shrink();
    }

    return Row(
      children: [
        Expanded(
          child:StatCard(
            title: 'Total Trades',
            value: stats.totalTrades.toString(),
            icon: Icons.swap_horiz,
          ),
        ),
        SizedBox(width: 12.w),
        Expanded(
          child: StatCard(
            title: 'Win Rate',
            value: '${stats.winRate.toStringAsFixed(1)}%',
            icon: Icons.show_chart,
            color: stats.winRate >= 50 ? AppTheme.successColor : AppTheme.warningColor,
          ),
        ),
        SizedBox(width: 12.w),
        Expanded(
          child: StatCard(
            title: 'Net PnL',
            value: '\$${stats.netPnl.toStringAsFixed(2)}',
            icon: stats.netPnl >= 0 ? Icons.trending_up : Icons.trending_down,
            color: stats.netPnl >= 0 ? AppTheme.successColor : AppTheme.dangerColor,
          ),
        ),
      ],
    );
  }

  Widget _buildPeriodSelector() {
    return SegmentedButton<String>(
      segments: const [
        ButtonSegment(value: 'today', label: Text('Today')),
        ButtonSegment(value: 'yesterday', label: Text('Yesterday')),
        ButtonSegment(value: 'week', label: Text('Week')),
        ButtonSegment(value: 'month', label: Text('Month')),
      ],
      selected: {_selectedPeriod},
      onSelectionChanged: (Set<String> newSelection) {
        setState(() {
          _selectedPeriod = newSelection.first;
        });
        context.read<TradeProvider>().fetchTradeStats(_selectedPeriod);
      },
    );
  }

  Widget _buildPositionCard(Trade trade) {
    final isProfit = trade.pnl != null && trade.pnl! >= 0;
    
    return Card(
      margin: EdgeInsets.only(bottom: 12.h),
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  trade.coinPair,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                  decoration: BoxDecoration(
                    color: trade.direction == 'LONG'
                        ? AppTheme.successColor.withValues(alpha: 0.2)
                        : AppTheme.dangerColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Text(
                    trade.direction,
                    style: TextStyle(
                      color: trade.direction == 'LONG'
                          ? AppTheme.successColor
                          : AppTheme.dangerColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 12.h),
            Row(
              children: [
                Expanded(
                  child: _buildDetailRow('Entry', '\$${trade.entryPrice.toStringAsFixed(4)}'),
                ),
                Expanded(
                  child: _buildDetailRow('Leverage', '${trade.leverage}x'),
                ),
              ],
            ),
            SizedBox(height: 8.h),
            Row(
              children: [
                Expanded(
                  child: _buildDetailRow('TP', '\$${trade.takeProfit.toStringAsFixed(4)}'),
                ),
                Expanded(
                  child: _buildDetailRow('SL', '\$${trade.stopLoss.toStringAsFixed(4)}'),
                ),
              ],
            ),
            SizedBox(height: 12.h),
            if (trade.pnl != null)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'PnL: \$${trade.pnl!.toStringAsFixed(2)} (${trade.pnlPercentage!.toStringAsFixed(2)}%)',
                    style: TextStyle(
                      color: isProfit ? AppTheme.successColor : AppTheme.dangerColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  ElevatedButton(
                    onPressed: () {
                      context.read<TradeProvider>().closeTrade(trade.id);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.dangerColor,
                      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
                    ),
                    child: const Text('Close'),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    );
  }

  Widget _buildEmptyState(String message) {
    return Container(
      padding: EdgeInsets.all(32.w),
      child: Column(
        children: [
          Icon(
            Icons.inbox_outlined,
            size: 64.sp,
            color: AppTheme.textSecondary,
          ),
          SizedBox(height: 16.h),
          Text(
            message,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color? color;

  const StatCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color ?? AppTheme.primaryColor, size: 24.sp),
          SizedBox(height: 8.h),
          Text(
            value,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 4.h),
          Text(
            title,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
