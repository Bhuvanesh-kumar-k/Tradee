import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/scanner_provider.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class ScannerTab extends StatefulWidget {
  const ScannerTab({super.key});

  @override
  State<ScannerTab> createState() => _ScannerTabState();
}

class _ScannerTabState extends State<ScannerTab> {
  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final scannerProvider = context.read<ScannerProvider>();
    await scannerProvider.fetchLiveMarketScan(force: false);
  }

  @override
  Widget build(BuildContext context) {
    final scannerProvider = context.watch<ScannerProvider>();

    return Column(
      children: [
        // Header with refresh button
        _buildHeader(scannerProvider),
        
        // Content
        Expanded(
          child: scannerProvider.isLoading
              ? _buildLoadingState()
              : scannerProvider.lastMarketScanData == null
                  ? _buildEmptyState('Tap Scan to analyze market')
                  : _buildMarketScanFeed(scannerProvider.lastMarketScanData!),
        ),
      ],
    );
  }

  Widget _buildHeader(ScannerProvider scannerProvider) {
    final btcTrend = scannerProvider.lastMarketScanData?['btc_macro_trend'] ?? 'NEUTRAL';
    final lastScanTime = scannerProvider.lastScanTime;
    
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        border: Border(
          bottom: BorderSide(color: AppTheme.primaryColor.withValues(alpha: 0.2)),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          'Market Scanner',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        SizedBox(width: 8.w),
                        IconButton(
                          icon: const Icon(Icons.rule, size: 20),
                          onPressed: () => showTradingRulesDialog(context),
                          color: AppTheme.textSecondary,
                        ),
                      ],
                    ),
                    SizedBox(height: 4.h),
                    Row(
                      children: [
                        _buildTrendPill('BTC 1D', btcTrend),
                        SizedBox(width: 8.w),
                        if (lastScanTime != null)
                          Text(
                            'Last Scanned: ${_formatScanTime(lastScanTime)}',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppTheme.textSecondary,
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              ElevatedButton.icon(
                onPressed: scannerProvider.isLoading ? null : _loadDataWithForce,
                icon: scannerProvider.isLoading
                    ? SizedBox(
                        width: 16.sp,
                        height: 16.sp,
                        child: const CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.refresh),
                label: const Text('Scan Now'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _loadDataWithForce() async {
    final scannerProvider = context.read<ScannerProvider>();
    await scannerProvider.fetchLiveMarketScan(force: true);
  }

  String _formatScanTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
    }
  }

  Widget _buildTrendPill(String label, String trend) {
    Color bgColor;
    Color textColor;
    
    if (trend == 'BULLISH') {
      bgColor = AppTheme.successColor.withValues(alpha: 0.2);
      textColor = AppTheme.successColor;
    } else if (trend == 'BEARISH') {
      bgColor = AppTheme.dangerColor.withValues(alpha: 0.2);
      textColor = AppTheme.dangerColor;
    } else {
      bgColor = AppTheme.textSecondary.withValues(alpha: 0.2);
      textColor = AppTheme.textSecondary;
    }
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Text(
        '$label: $trend',
        style: TextStyle(
          color: textColor,
          fontSize: 11.sp,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: AppTheme.primaryColor),
          SizedBox(height: 16.h),
          Text(
            'Scanning market...',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMarketScanFeed(Map<String, dynamic> data) {
    final coins = List<Map<String, dynamic>>.from(data['coins'] ?? []);
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Coin Status Feed',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          SizedBox(height: 12.h),
          ...coins.map((coin) => _buildCoinCard(coin)).toList(),
        ],
      ),
    );
  }

  Widget _buildCoinCard(Map<String, dynamic> coin) {
    final coinPair = coin['coin_pair'] ?? '';
    final macro1d = coin['macro_1d_trend'] ?? 'NEUTRAL';
    final ltf1h = coin['ltf_1h_trend'] ?? 'NEUTRAL';
    final hasValidSetup = coin['has_valid_setup'] ?? false;
    final timeframeDetails = List<Map<String, dynamic>>.from(coin['timeframe_details'] ?? []);
    
    Color cardColor;
    if (hasValidSetup) {
      cardColor = AppTheme.successColor.withValues(alpha: 0.1);
    } else if (macro1d == 'BEARISH') {
      cardColor = AppTheme.dangerColor.withValues(alpha: 0.1);
    } else {
      cardColor = AppTheme.cardColor;
    }
    
    return Card(
      margin: EdgeInsets.only(bottom: 12.h),
      color: cardColor,
      child: ExpansionTile(
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              coinPair,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            Row(
              children: [
                _buildTrendPill('1D', macro1d),
                SizedBox(width: 4.w),
                _buildTrendPill('1H', ltf1h),
              ],
            ),
          ],
        ),
        subtitle: hasValidSetup
            ? Text(
                '✓ Valid setup detected',
                style: TextStyle(
                  color: AppTheme.successColor,
                  fontWeight: FontWeight.bold,
                  fontSize: 12.sp,
                ),
              )
            : null,
        children: [
          Padding(
            padding: EdgeInsets.all(16.w),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Timeframe Analysis',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 12.h),
                ...timeframeDetails.map((tf) => _buildMiniTimeframeDetail(tf)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniTimeframeDetail(Map<String, dynamic> tf) {
    final direction = tf['direction'] ?? 'NEUTRAL';
    final failedChecks = List<String>.from(tf['failed_checks'] ?? []);
    
    return Container(
      margin: EdgeInsets.only(bottom: 8.h),
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                tf['timeframe'],
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: direction == 'LONG'
                      ? AppTheme.successColor.withValues(alpha: 0.2)
                      : direction == 'SHORT'
                          ? AppTheme.dangerColor.withValues(alpha: 0.2)
                          : AppTheme.textSecondary.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Text(
                  direction,
                  style: TextStyle(
                    color: direction == 'LONG'
                        ? AppTheme.successColor
                        : direction == 'SHORT'
                            ? AppTheme.dangerColor
                            : AppTheme.textSecondary,
                    fontSize: 11.sp,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          if (failedChecks.isNotEmpty) ...[
            SizedBox(height: 6.h),
            Text(
              'Failed: ${failedChecks.take(2).join(", ")}${failedChecks.length > 2 ? "..." : ""}',
              style: TextStyle(
                color: AppTheme.dangerColor,
                fontSize: 10.sp,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildEmptyState(String message) {
    return Container(
      padding: EdgeInsets.all(32.w),
      child: Column(
        children: [
          Icon(
            Icons.radar_outlined,
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

  void showTradingRulesDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF161B22),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.75,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        expand: false,
        builder: (context, scrollController) => Padding(
          padding: const EdgeInsets.all(20.0),
          child: ListView(
            controller: scrollController,
            children: [
              Row(
                children: const [
                  Icon(Icons.verified_outlined, color: Color(0xFF00D4AA), size: 24),
                  SizedBox(width: 10),
                  Text(
                    'Trading Criteria & Checks',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                'Before any trade is approved or taken by our engine, it must strictly pass these multi-timeframe quantitative filters:',
                style: TextStyle(color: Color(0xFF8B949E), fontSize: 13),
              ),
              const SizedBox(height: 16),
              _buildRuleItem('1. Macro Trend Confluence (1D)', 'Bitcoin (BTC) and the selected coin must align with EMA 50 & EMA 200 on 1D candles.'),
              _buildRuleItem('2. Execution Alignment (1H)', 'Lower timeframe candle close must align with EMA 50 (above for LONG, below for SHORT).'),
              _buildRuleItem('3. ADX >= 20 (Non-Choppy)', 'Average Directional Index must confirm genuine trend momentum rather than sideways whipsaw.'),
              _buildRuleItem('4. RSI Pullback Zone', 'Relative Strength Index (RSI 14) must reside between 40-60 to prevent buying at exhaustion peaks.'),
              _buildRuleItem('5. Volume Confirmation (>= 80% SMA20)', 'Candle volume must confirm liquidity and support at least 80% of its 20-period moving average.'),
              _buildRuleItem('6. Liquidation Buffer (Safe Distance)', 'Stop-loss distance must maintain >= 40% margin clearance from isolated liquidation price.'),
              _buildRuleItem('7. MACD Momentum (Liberal Gate)', 'MACD histogram expansion is checked. If MACD fails but all other criteria pass, setup is tagged HIGH-RISK and leverage is bounded to 5x.', isLiberal: true),
              _buildRuleItem('8. Minimum Net ROI >= 20%', 'After accounting for taker fees and slippage buffers, minimum projected ROI to TP must meet or exceed 20%.'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRuleItem(String title, String description, {bool isLiberal = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isLiberal ? const Color(0xFFD29922).withOpacity(0.1) : const Color(0xFF0D1117),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isLiberal ? const Color(0xFFD29922) : const Color(0xFF30363D),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: isLiberal ? const Color(0xFFD29922) : const Color(0xFF00D4AA),
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                if (isLiberal) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFFD29922),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text('LIBERAL', style: TextStyle(color: Colors.black, fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 4),
            Text(description, style: const TextStyle(color: Color(0xFFE6EDF3), fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
