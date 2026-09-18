import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class TelegramTab extends StatefulWidget {
  const TelegramTab({super.key});

  @override
  State<TelegramTab> createState() => _TelegramTabState();
}

class _TelegramTabState extends State<TelegramTab> {
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
        border: Border.all(color: AppTheme.primaryColor.withOpacity(0.3)),
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
                  color: AppTheme.textSecondary.withOpacity(0.2),
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
    // Placeholder signals
    final signals = [
      {
        'coin': 'BTC/USDT',
        'direction': 'LONG',
        'leverage': '10x',
        'entry': '67500',
        'tp': '69000',
        'sl': '66500',
        'channel': 'CryptoSignals Pro',
        'ai_verdict': 'APPROVED',
        'ai_confidence': 0.85,
        'time': '2 hours ago',
      },
      {
        'coin': 'ETH/USDT',
        'direction': 'SHORT',
        'leverage': '8x',
        'entry': '3450',
        'tp': '3350',
        'sl': '3500',
        'channel': 'Premium Crypto',
        'ai_verdict': 'REJECTED',
        'ai_confidence': 0.72,
        'time': '5 hours ago',
      },
    ];

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: signals.length,
      itemBuilder: (context, index) {
        return _buildSignalCard(signals[index]);
      },
    );
  }

  Widget _buildSignalCard(Map<String, dynamic> signal) {
    final isApproved = signal['ai_verdict'] == 'APPROVED';
    
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
                  signal['coin'],
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                  decoration: BoxDecoration(
                    color: signal['direction'] == 'LONG'
                        ? AppTheme.successColor.withOpacity(0.2)
                        : AppTheme.dangerColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Text(
                    signal['direction'],
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
            SizedBox(height: 12.h),
            Row(
              children: [
                Expanded(
                  child: _buildDetailRow('Entry', '\$${signal['entry']}'),
                ),
                Expanded(
                  child: _buildDetailRow('Leverage', signal['leverage']),
                ),
              ],
            ),
            SizedBox(height: 8.h),
            Row(
              children: [
                Expanded(
                  child: _buildDetailRow('TP', '\$${signal['tp']}'),
                ),
                Expanded(
                  child: _buildDetailRow('SL', '\$${signal['sl']}'),
                ),
              ],
            ),
            SizedBox(height: 12.h),
            Container(
              padding: EdgeInsets.all(12.w),
              decoration: BoxDecoration(
                color: isApproved
                    ? AppTheme.successColor.withOpacity(0.1)
                    : AppTheme.dangerColor.withOpacity(0.1),
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
                        'AI Verdict: ${signal['ai_verdict']}',
                        style: TextStyle(
                          color: isApproved ? AppTheme.successColor : AppTheme.dangerColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 4.h),
                  Text(
                    'Confidence: ${(signal['ai_confidence'] * 100).toStringAsFixed(0)}%',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            SizedBox(height: 8.h),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  signal['channel'],
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
                Text(
                  signal['time'],
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
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
}
