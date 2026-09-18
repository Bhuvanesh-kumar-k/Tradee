import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/scanner_provider.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class SingleCoinTab extends StatefulWidget {
  const SingleCoinTab({super.key});

  @override
  State<SingleCoinTab> createState() => _SingleCoinTabState();
}

class _SingleCoinTabState extends State<SingleCoinTab> {
  final _coinController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  Map<String, dynamic>? _analysisResult;

  @override
  void dispose() {
    _coinController.dispose();
    super.dispose();
  }

  Future<void> _analyzeCoin() async {
    if (!_formKey.currentState!.validate()) return;

    final scannerProvider = context.read<ScannerProvider>();
    final result = await scannerProvider.checkCoin(_coinController.text.trim());
    
    if (mounted) {
      setState(() {
        _analysisResult = result;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scannerProvider = context.watch<ScannerProvider>();

    return SingleChildScrollView(
      padding: EdgeInsets.all(16.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Single Coin Analysis',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 16.h),
          
          // Search Input
          Form(
            key: _formKey,
            child: Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _coinController,
                    decoration: const InputDecoration(
                      labelText: 'Coin Symbol (e.g., BTC, ETH)',
                      prefixIcon: Icon(Icons.search),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Enter coin symbol';
                      }
                      return null;
                    },
                  ),
                ),
                SizedBox(width: 12.w),
                ElevatedButton(
                  onPressed: scannerProvider.isLoading ? null : _analyzeCoin,
                  child: scannerProvider.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Analyze'),
                ),
              ],
            ),
          ),
          
          SizedBox(height: 24.h),
          
          // Analysis Result
          if (_analysisResult != null)
            _buildAnalysisResult(_analysisResult!)
          else
            _buildEmptyState('Enter a coin symbol to analyze'),
        ],
      ),
    );
  }

  Widget _buildAnalysisResult(Map<String, dynamic> result) {
    final overallSignal = result['overall_signal'];
    
    return Card(
      child: Padding(
        padding: EdgeInsets.all(20.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  result['coin_pair'],
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                if (overallSignal != null && overallSignal != 'NONE')
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
                    decoration: BoxDecoration(
                      color: overallSignal == 'LONG'
                          ? AppTheme.successColor.withValues(alpha: 0.2)
                          : AppTheme.dangerColor.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                    child: Text(
                      overallSignal,
                      style: TextStyle(
                        color: overallSignal == 'LONG'
                            ? AppTheme.successColor
                            : AppTheme.dangerColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 16.sp,
                      ),
                    ),
                  ),
              ],
            ),
            
            if (overallSignal != null && overallSignal != 'NONE') ...[
              SizedBox(height: 20.h),
              _buildTradeDetails(result),
            ],
            
            SizedBox(height: 20.h),
            Text(
              'Timeframe Analysis',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            SizedBox(height: 12.h),
            ...List.generate(
              result['timeframes'].length,
              (index) => _buildTimeframeCard(result['timeframes'][index]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTradeDetails(Map<String, dynamic> result) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Column(
        children: [
          _buildDetailRow('Entry Price', '\$${result['entry_price']?.toStringAsFixed(4)}'),
          _buildDetailRow('Take Profit', '\$${result['take_profit']?.toStringAsFixed(4)}'),
          _buildDetailRow('Stop Loss', '\$${result['stop_loss']?.toStringAsFixed(4)}'),
          _buildDetailRow('Leverage', '${result['leverage']}x'),
          _buildDetailRow('Expected ROI', '${(result['expected_roi']! * 100).toStringAsFixed(1)}%'),
        ],
      ),
    );
  }

  Widget _buildTimeframeCard(Map<String, dynamic> tf) {
    final direction = tf['direction'];
    final roi = tf['roi'];
    
    return Card(
      margin: EdgeInsets.only(bottom: 8.h),
      child: Padding(
        padding: EdgeInsets.all(12.w),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              tf['timeframe'],
              style: Theme.of(context).textTheme.titleMedium,
            ),
            if (direction != null)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: direction == 'LONG'
                      ? AppTheme.successColor.withValues(alpha: 0.2)
                      : AppTheme.dangerColor.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8.r),
                ),
                child: Text(
                  direction,
                  style: TextStyle(
                    color: direction == 'LONG'
                        ? AppTheme.successColor
                        : AppTheme.dangerColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            if (roi != null)
              Text(
                '${(roi * 100).toStringAsFixed(1)}% ROI',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4.h),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
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
            Icons.search_off,
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
