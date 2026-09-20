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
    await scannerProvider.scanAllCoins();
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
              : scannerProvider.marketScanData.isEmpty
                  ? _buildEmptyState('Tap Scan to analyze market')
                  : _buildMarketScanFeed(scannerProvider.marketScanData),
        ),
      ],
    );
  }

  Widget _buildHeader(ScannerProvider scannerProvider) {
    final btcTrend = scannerProvider.marketScanData['btc_macro_trend'] ?? 'NEUTRAL';
    
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
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Market Scanner',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  SizedBox(height: 4.h),
                  Row(
                    children: [
                      _buildTrendPill('BTC 1D', btcTrend),
                      SizedBox(width: 8.w),
                      Text(
                        'Open Slots: 3/3',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              ElevatedButton.icon(
                onPressed: scannerProvider.isLoading ? null : _loadData,
                icon: scannerProvider.isLoading
                    ? SizedBox(
                        width: 16.sp,
                        height: 16.sp,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
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
}
