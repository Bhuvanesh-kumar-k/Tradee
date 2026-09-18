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
    await Future.wait([
      scannerProvider.fetchStatus(),
      scannerProvider.fetchLogs(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final scannerProvider = context.watch<ScannerProvider>();

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Card
            _buildStatusCard(scannerProvider.status),
            SizedBox(height: 16.h),
            
            // Scanner Logs
            Text(
              'Live Scanner Logs',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 12.h),
            scannerProvider.logs.isEmpty
                ? _buildEmptyState('No scanner logs yet')
                : ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: scannerProvider.logs.length,
                    itemBuilder: (context, index) {
                      return _buildLogCard(scannerProvider.logs[index]);
                    },
                  ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(Map<String, dynamic> status) {
    final isFrozen = status['status'] == 'frozen';
    
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: isFrozen 
            ? AppTheme.warningColor.withValues(alpha: 0.2)
            : AppTheme.successColor.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(
          color: isFrozen ? AppTheme.warningColor : AppTheme.successColor,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isFrozen ? Icons.pause_circle_outline : Icons.play_circle_outline,
                color: isFrozen ? AppTheme.warningColor : AppTheme.successColor,
              ),
              SizedBox(width: 8.w),
              Text(
                isFrozen ? 'Scanner Paused' : 'Scanner Active',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ],
          ),
          SizedBox(height: 8.h),
          Text(
            status['message'] ?? 'System operating normally',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          if (status['upcoming_events'] != null && status['upcoming_events'].isNotEmpty)
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 12.h),
                Text(
                  'Upcoming Events:',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 8.h),
                ...List.generate(
                  status['upcoming_events'].take(3).length,
                  (index) => Padding(
                    padding: EdgeInsets.only(bottom: 4.h),
                    child: Text(
                      '• ${status['upcoming_events'][index]['name']} at ${status['upcoming_events'][index]['time_ist']}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildLogCard(ScannerLog log) {
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
                  log.coinPair,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                  decoration: BoxDecoration(
                    color: AppTheme.cardColor,
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Text(
                    log.timeframe,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
            SizedBox(height: 12.h),
            Row(
              children: [
                _buildIndicatorBadge('Trend', log.trendStatus),
                SizedBox(width: 8.w),
                _buildIndicatorBadge('Signal', log.signalDetected),
              ],
            ),
            if (log.indicatorValues != null) ...[
              SizedBox(height: 12.h),
              Wrap(
                spacing: 8.w,
                runSpacing: 8.h,
                children: [
                  _buildIndicatorChip('RSI', log.indicatorValues!['rsi']?.toStringAsFixed(1)),
                  _buildIndicatorChip('ADX', log.indicatorValues!['adx']?.toStringAsFixed(1)),
                  _buildIndicatorChip('MACD', log.indicatorValues!['macd_hist']?.toStringAsFixed(3)),
                ],
              ),
            ],
            SizedBox(height: 8.h),
            Text(
              _formatTime(log.scanTime),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIndicatorBadge(String label, String? value) {
    if (value == null) return const SizedBox.shrink();
    
    Color color;
    if (value == 'BULLISH' || value == 'LONG') {
      color = AppTheme.successColor;
    } else if (value == 'BEARISH' || value == 'SHORT') {
      color = AppTheme.dangerColor;
    } else {
      color = AppTheme.textSecondary;
    }
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: Text(
        '$label: $value',
        style: TextStyle(
          color: color,
          fontSize: 12.sp,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildIndicatorChip(String label, String? value) {
    if (value == null) return const SizedBox.shrink();
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: Text(
        '$label: $value',
        style: Theme.of(context).textTheme.bodySmall,
      ),
    );
  }

  String _formatTime(DateTime dateTime) {
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
