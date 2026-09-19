import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';
import 'package:crypto_trading_app/utils/theme.dart' show AppTheme;

class TelegramTab extends StatefulWidget {
  const TelegramTab({super.key});

  @override
  State<TelegramTab> createState() => _TelegramTabState();
}

class _TelegramTabState extends State<TelegramTab> {
  List<dynamic> _signals = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadSignals();
  }

  Future<void> _loadSignals() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final response = await ApiClient.get(Constants.telegramSignals);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _signals = data['signals'] ?? [];
      }
    } catch (_) {
      _signals = [];
    }
    if (mounted) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status Card
          _buildStatusCard(),
          SizedBox(height: 16.h),
          
          // Signals Feed
          Text(
            'Telegram Signals & AI Analysis',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 12.h),
          _buildSignalsList(),
        ],
      ),
    );
  }

  Widget _buildStatusCard() {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.telegram_outlined, color: AppTheme.primaryColor),
              SizedBox(width: 8.w),
              Text(
                'Telegram Listener',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: AppTheme.textSecondary.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8.r),
                ),
                child: Text(
                  'Not Configured',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ],
          ),
          SizedBox(height: 12.h),
          Text(
            'Configure Telegram credentials in Settings to enable signal listening',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSignalsList() {
    if (_isLoading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32.0),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_signals.isEmpty) {
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
              'No Signals Yet. Connect Telegram in Settings or trigger a Market Scan.',
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _signals.length,
      itemBuilder: (context, index) {
        return _buildSignalCard(_signals[index]);
      },
    );
  }

  Widget _buildSignalCard(Map<String, dynamic> signal) {
    final isApproved = signal['ai_verdict'] == 'APPROVED';
    final sourceType = signal['source_type'] ?? 'telegram'; // 'telegram' or 'strategy'
    final channelName = signal['channel_name'] ?? 'Unknown Channel';
    final confidence = (signal['ai_confidence'] ?? 0.0) as double;
    final analysis = signal['analysis'] as Map<String, dynamic>? ?? {};
    
    return Card(
      margin: EdgeInsets.only(bottom: 12.h),
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with coin and direction
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  signal['coin_pair'] ?? signal['coin'] ?? 'Unknown',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                  decoration: BoxDecoration(
                    color: signal['direction'] == 'LONG'
                        ? AppTheme.successColor.withValues(alpha: 0.2)
                        : AppTheme.dangerColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Text(
                    signal['direction'] ?? 'UNKNOWN',
                    style: TextStyle(
                      color: signal['direction'] == 'LONG'
                          ? AppTheme.successColor
                          : AppTheme.dangerColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 8.h),
            
            // Source Origin Tag
            Container(
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8.r),
              ),
              child: Text(
                sourceType == 'telegram' 
                    ? 'Source: Telegram Channel ($channelName)'
                    : 'Source: App Strategy Engine',
                style: TextStyle(
                  color: AppTheme.primaryColor,
                  fontSize: 11.sp,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            SizedBox(height: 12.h),
            
            // Entry, Leverage, TP, SL
            Row(
              children: [
                Expanded(
                  child: _buildDetailRow('Entry', '\$${signal['entry'] ?? 'N/A'}'),
                ),
                Expanded(
                  child: _buildDetailRow('Leverage', '${signal['leverage'] ?? 'N/A'}x'),
                ),
              ],
            ),
            SizedBox(height: 8.h),
            Row(
              children: [
                Expanded(
                  child: _buildDetailRow('TP', '\$${signal['tp'] ?? 'N/A'}'),
                ),
                Expanded(
                  child: _buildDetailRow('SL', '\$${signal['sl'] ?? 'N/A'}'),
                ),
              ],
            ),
            SizedBox(height: 12.h),
            
            // AI Verdict Card
            Container(
              padding: EdgeInsets.all(12.w),
              decoration: BoxDecoration(
                color: isApproved
                    ? AppTheme.successColor.withValues(alpha: 0.1)
                    : AppTheme.dangerColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8.r),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        isApproved ? Icons.check_circle : Icons.cancel,
                        color: isApproved ? AppTheme.successColor : AppTheme.dangerColor,
                        size: 16.sp,
                      ),
                      SizedBox(width: 8.w),
                      Text(
                        'AI Verdict: ${signal['ai_verdict'] ?? 'UNKNOWN'}',
                        style: TextStyle(
                          color: isApproved ? AppTheme.successColor : AppTheme.dangerColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(width: 8.w),
                      Text(
                        '(${(confidence * 100).toStringAsFixed(0)}%)',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            SizedBox(height: 12.h),
            
            // Expandable Analysis Details
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: Text(
                'View Analysis Details',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.primaryColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
              children: [
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 8.h),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildAnalysisItem('Multi-timeframe Trend', analysis['multi_timeframe_trend'] ?? 'N/A'),
                      _buildAnalysisItem('EMA50/EMA200 Status', analysis['ema_status'] ?? 'N/A'),
                      _buildAnalysisItem('ADX Trend Strength', analysis['adx_strength'] ?? 'N/A'),
                      _buildAnalysisItem('RSI Pullback Zone', analysis['rsi_zone'] ?? 'N/A'),
                      SizedBox(height: 8.h),
                      Text(
                        'Reason: ${analysis['reason'] ?? 'No reason provided'}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          fontStyle: FontStyle.italic,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            // Timestamp
            if (signal['created_at'] != null)
              Padding(
                padding: EdgeInsets.only(top: 8.h),
                child: Text(
                  signal['created_at'],
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalysisItem(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 2.h),
      child: Row(
        children: [
          Text(
            '$label: ',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ],
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
}
