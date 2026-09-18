import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:crypto_trading_app/utils/api_client.dart';
import 'package:crypto_trading_app/utils/constants.dart';

class Trade {
  final int id;
  final String coinPair;
  final String direction;
  final double entryPrice;
  final int leverage;
  final double marginUsed;
  final double takeProfit;
  final double stopLoss;
  final double liquidationPrice;
  final double expectedNetRoi;
  final String timeframe;
  final String status;
  final double? pnl;
  final double? pnlPercentage;
  
  Trade({
    required this.id,
    required this.coinPair,
    required this.direction,
    required this.entryPrice,
    required this.leverage,
    required this.marginUsed,
    required this.takeProfit,
    required this.stopLoss,
    required this.liquidationPrice,
    required this.expectedNetRoi,
    required this.timeframe,
    required this.status,
    this.pnl,
    this.pnlPercentage,
  });
  
  factory Trade.fromJson(Map<String, dynamic> json) {
    return Trade(
      id: json['id'],
      coinPair: json['coin_pair'],
      direction: json['direction'],
      entryPrice: json['entry_price'].toDouble(),
      leverage: json['leverage'],
      marginUsed: json['margin_used'].toDouble(),
      takeProfit: json['take_profit'].toDouble(),
      stopLoss: json['stop_loss'].toDouble(),
      liquidationPrice: json['liquidation_price'].toDouble(),
      expectedNetRoi: json['expected_net_roi'].toDouble(),
      timeframe: json['timeframe'],
      status: json['status'],
      pnl: json['pnl']?.toDouble(),
      pnlPercentage: json['pnl_percentage']?.toDouble(),
    );
  }
}

class TradeStats {
  final int totalTrades;
  final int winCount;
  final int lossCount;
  final double winRate;
  final double netPnl;
  
  TradeStats({
    required this.totalTrades,
    required this.winCount,
    required this.lossCount,
    required this.winRate,
    required this.netPnl,
  });
  
  factory TradeStats.fromJson(Map<String, dynamic> json) {
    return TradeStats(
      totalTrades: json['total_trades'],
      winCount: json['win_count'],
      lossCount: json['loss_count'],
      winRate: json['win_rate'].toDouble(),
      netPnl: json['net_pnl'].toDouble(),
    );
  }
}

class TradeProvider with ChangeNotifier {
  List<Trade> _activeTrades = [];
  List<Trade> _tradeHistory = [];
  TradeStats? _stats;
  bool _isLoading = false;
  String? _errorMessage;
  
  List<Trade> get activeTrades => _activeTrades;
  List<Trade> get tradeHistory => _tradeHistory;
  TradeStats? get stats => _stats;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  
  Future<void> fetchActiveTrades() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.get(Constants.activeTrades);
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        _activeTrades = data.map((json) => Trade.fromJson(json)).toList();
        _isLoading = false;
        notifyListeners();
      } else {
        _errorMessage = 'Failed to fetch active trades';
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> fetchTradeHistory() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.get('${Constants.tradeHistory}?limit=50');
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        _tradeHistory = data.map((json) => Trade.fromJson(json)).toList();
        _isLoading = false;
        notifyListeners();
      } else {
        _errorMessage = 'Failed to fetch trade history';
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> fetchTradeStats(String period) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.get('${Constants.tradeStats}?period=$period');
      
      if (response.statusCode == 200) {
        _stats = TradeStats.fromJson(jsonDecode(response.body));
        _isLoading = false;
        notifyListeners();
      } else {
        _errorMessage = 'Failed to fetch trade stats';
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<bool> closeTrade(int tradeId) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await ApiClient.post(
        Constants.closeTrade,
        body: {'trade_id': tradeId},
      );
      
      if (response.statusCode == 200) {
        await fetchActiveTrades();
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _errorMessage = 'Failed to close trade';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
