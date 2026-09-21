import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:provider/provider.dart';
import 'package:crypto_trading_app/providers/scanner_provider.dart';
import 'package:crypto_trading_app/utils/theme.dart';

class UpperCaseTextFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    return TextEditingValue(
      text: newValue.text.toUpperCase(),
      selection: newValue.selection,
    );
  }
}

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
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Single Coin Analysis',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              IconButton(
                icon: const Icon(Icons.rule, size: 20),
                onPressed: () => showTradingRulesDialog(context),
                color: AppTheme.textSecondary,
              ),
            ],
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
    final overallSignal = result['overall_signal'] ?? 'NEUTRAL';
    final macro1dTrend = result['macro_1d_trend'] ?? 'NEUTRAL';
    final ltf1hTrend = result['ltf_1h_trend'] ?? 'NEUTRAL';
    final btcMacroTrend = result['btc_macro_trend'] ?? 'NEUTRAL';
    final summaryReason = result['summary_reason'] ?? '';
    
    return Card(
      child: Padding(
        padding: EdgeInsets.all(20.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Coin Pair Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  result['coin_pair'],
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                if (overallSignal != 'NEUTRAL')
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
            
            SizedBox(height: 16.h),
            
            // Macro Status Header Card
            _buildMacroStatusCard(macro1dTrend, ltf1hTrend, btcMacroTrend),
            
            SizedBox(height: 16.h),
            
            // Warning box if no signal
            if (overallSignal == 'NEUTRAL' || overallSignal == 'NONE')
              _buildWarningBox(summaryReason),
            
            // Trade details if valid signal
            if (overallSignal == 'LONG' || overallSignal == 'SHORT') ...[
              SizedBox(height: 16.h),
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

  Widget _buildMacroStatusCard(String macro1d, String ltf1h, String btcMacro) {
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
          Text(
            'Market Status',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 12.h),
          Wrap(
            spacing: 8.w,
            runSpacing: 8.h,
            children: [
              _buildTrendPill('1D Macro', macro1d),
              _buildTrendPill('1H LTF', ltf1h),
              _buildTrendPill('BTC Macro', btcMacro),
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
          fontSize: 12.sp,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildWarningBox(String reason) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: Colors.orange.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: Colors.orange.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 20.sp),
              SizedBox(width: 8.w),
              Text(
                'No trade recommended',
                style: TextStyle(
                  color: Colors.orange,
                  fontWeight: FontWeight.bold,
                  fontSize: 14.sp,
                ),
              ),
            ],
          ),
          SizedBox(height: 8.h),
          Text(
            reason,
            style: TextStyle(
              color: Colors.orange.shade700,
              fontSize: 12.sp,
            ),
          ),
        ],
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
    final direction = tf['direction'] ?? 'NEUTRAL';
    final isSetupValid = tf['is_setup_valid'] ?? false;
    final passedChecks = List<String>.from(tf['passed_checks'] ?? []);
    final failedChecks = List<String>.from(tf['failed_checks'] ?? []);
    final roi = tf['roi'];
    
    return Card(
      margin: EdgeInsets.only(bottom: 12.h),
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with timeframe and direction
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  tf['timeframe'],
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
                  decoration: BoxDecoration(
                    color: direction == 'LONG'
                        ? AppTheme.successColor.withValues(alpha: 0.2)
                        : direction == 'SHORT'
                            ? AppTheme.dangerColor.withValues(alpha: 0.2)
                            : AppTheme.textSecondary.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Text(
                    direction,
                    style: TextStyle(
                      color: direction == 'LONG'
                          ? AppTheme.successColor
                          : direction == 'SHORT'
                              ? AppTheme.dangerColor
                              : AppTheme.textSecondary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.sp,
                    ),
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 12.h),
            
            // Passed checks
            if (passedChecks.isNotEmpty) ...[
              Text(
                'Passed Checks',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.successColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 6.h),
              Wrap(
                spacing: 6.w,
                runSpacing: 6.h,
                children: passedChecks.map((check) => _buildCheckChip(check, true)).toList(),
              ),
              SizedBox(height: 8.h),
            ],
            
            // Failed checks
            if (failedChecks.isNotEmpty) ...[
              Text(
                'Failed Checks',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.dangerColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 6.h),
              Wrap(
                spacing: 6.w,
                runSpacing: 6.h,
                children: failedChecks.map((check) => _buildCheckChip(check, false)).toList(),
              ),
            ],
            
            // ROI if valid setup
            if (isSetupValid && roi != null) ...[
              SizedBox(height: 12.h),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
                decoration: BoxDecoration(
                  color: AppTheme.successColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8.r),
                ),
                child: Text(
                  'Expected ROI: ${(roi * 100).toStringAsFixed(1)}%',
                  style: TextStyle(
                    color: AppTheme.successColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 14.sp,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildCheckChip(String check, bool passed) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: passed
            ? AppTheme.successColor.withValues(alpha: 0.15)
            : AppTheme.dangerColor.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            passed ? Icons.check_circle : Icons.cancel,
            size: 12.sp,
            color: passed ? AppTheme.successColor : AppTheme.dangerColor,
          ),
          SizedBox(width: 4.w),
          Text(
            check,
            style: TextStyle(
              color: passed ? AppTheme.successColor : AppTheme.dangerColor,
              fontSize: 11.sp,
            ),
          ),
        ],
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
          color: isLiberal ? const Color(0xFFD29922).withValues(alpha: 0.1) : const Color(0xFF0D1117),
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
