import 'package:flutter/material.dart';
import 'package:crypto_trading_app/utils/theme.dart';

void showTradingRulesDialog(BuildContext context) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppTheme.cardColor,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (context) => DraggableScrollableSheet(
      initialChildSize: 0.8,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      expand: false,
      builder: (context, scrollController) => Padding(
        padding: const EdgeInsets.all(20.0),
        child: ListView(
          controller: scrollController,
          children: [
            Row(
              children: [
                Icon(Icons.rule_folder_outlined, color: AppTheme.primaryColor, size: 24),
                const SizedBox(width: 10),
                const Text(
                  'Trading Criteria & Checks',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Text(
              'Before any setup is approved by the algorithmic engine, it must pass these strict multi-timeframe quantitative gates:',
              style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 16),
            _buildRuleItem('1. Macro Trend Confluence (1D)', 'Bitcoin (BTC) and the selected coin must both trade aligned with EMA 50 & EMA 200 on 1D daily candles.'),
            _buildRuleItem('2. Execution Confirmation (1H)', 'Lower timeframe 1-hour candle close must confirm trend direction relative to its EMA 50.'),
            _buildRuleItem('3. ADX >= 20 (Non-Choppy Filter)', 'Average Directional Index (ADX 14) must meet or exceed 20 to eliminate sideways whipsaw markets.'),
            _buildRuleItem('4. RSI Pullback / Breakdown Zone', 'RSI (14) must reside between 40-60 on closed bars to prevent buying at exhaustion peaks.'),
            _buildRuleItem('5. Volume Confirmation (>= 80% SMA20)', 'Candle volume must confirm liquidity and support at least 80% of its 20-period moving average.'),
            _buildRuleItem('6. Liquidation Buffer (Safe Distance)', 'Stop-loss distance must maintain >= 40% margin clearance from isolated liquidation price.'),
            _buildRuleItem('7. MACD Momentum (Liberal Gate)', 'MACD histogram expansion is evaluated. If MACD fails but all other criteria pass, setup is tagged HIGH-RISK and leverage is bounded to 5x.', isLiberal: true),
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
        color: isLiberal ? AppTheme.warningColor.withValues(alpha: 0.1) : AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isLiberal ? AppTheme.warningColor : const Color(0xFF30363D),
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
                  color: isLiberal ? AppTheme.warningColor : AppTheme.primaryColor,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              if (isLiberal) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppTheme.warningColor,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text('LIBERAL', style: TextStyle(color: Colors.black, fontSize: 10, fontWeight: FontWeight.bold)),
                ),
              ],
            ],
          ),
          const SizedBox(height: 6),
          Text(description, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 12)),
        ],
      ),
    ),
  );
}
