"""
Streaming Backtest Service with Progressive Loading
Yields results as they complete for real-time UI updates
"""

import json
from crypto_backtest_service import CryptoBacktestService
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class StreamingBacktestService:
    """Service for streaming backtest results progressively"""
    
    def __init__(self, db_config):
        self.backtest_service = CryptoBacktestService(db_config)
    
    def stream_strategy_against_all_cryptos(self, strategy_id, parameters, 
                                           start_date=None, end_date=None, 
                                           interval='1d', use_daily_sampling=True,
                                           max_workers=4):
        """
        Stream backtest results as they complete
        
        Yields:
            dict: Progress updates and completed results in SSE format
        """
        try:
            # Get all cryptocurrencies with data
            cryptos = self.backtest_service.get_cryptocurrencies_with_data()
            total_cryptos = len(cryptos)
            
            if total_cryptos == 0:
                yield self._format_sse({
                    'type': 'error',
                    'message': 'No cryptocurrencies with data found'
                })
                return
            
            # Send initial status
            yield self._format_sse({
                'type': 'start',
                'total': total_cryptos,
                'message': f'Starting backtest for {total_cryptos} cryptocurrencies...'
            })
            
            completed = 0
            successful = 0
            failed = 0
            results = []
            start_time = time.time()
            
            # Use thread pool for parallel execution
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_crypto = {
                    executor.submit(
                        self._run_single_backtest_safe,
                        strategy_id,
                        crypto,
                        parameters,
                        start_date,
                        end_date,
                        interval,
                        use_daily_sampling
                    ): crypto
                    for crypto in cryptos
                }
                
                # Process results as they complete
                for future in as_completed(future_to_crypto):
                    crypto = future_to_crypto[future]
                    completed += 1
                    
                    try:
                        result = future.result()
                        
                        if result.get('success', False):
                            successful += 1
                            results.append(result)
                            
                            # Send successful result
                            yield self._format_sse({
                                'type': 'result',
                                'data': result,
                                'progress': {
                                    'completed': completed,
                                    'total': total_cryptos,
                                    'successful': successful,
                                    'failed': failed,
                                    'percent': round((completed / total_cryptos) * 100, 1)
                                }
                            })
                        else:
                            failed += 1
                            
                            # Send failure notification
                            yield self._format_sse({
                                'type': 'progress',
                                'message': f'Failed: {crypto["symbol"]}',
                                'progress': {
                                    'completed': completed,
                                    'total': total_cryptos,
                                    'successful': successful,
                                    'failed': failed,
                                    'percent': round((completed / total_cryptos) * 100, 1)
                                }
                            })
                    
                    except Exception as e:
                        failed += 1
                        yield self._format_sse({
                            'type': 'error',
                            'message': f'Error processing {crypto["symbol"]}: {str(e)}',
                            'progress': {
                                'completed': completed,
                                'total': total_cryptos,
                                'successful': successful,
                                'failed': failed,
                                'percent': round((completed / total_cryptos) * 100, 1)
                            }
                        })
            
            # Calculate final summary
            elapsed_time = time.time() - start_time
            summary = self._calculate_summary(results, total_cryptos, successful, failed)
            
            # Send completion event
            yield self._format_sse({
                'type': 'complete',
                'summary': summary,
                'elapsed_time': round(elapsed_time, 2),
                'message': f'Completed {total_cryptos} backtests in {elapsed_time:.1f}s'
            })
            
        except Exception as e:
            yield self._format_sse({
                'type': 'error',
                'message': f'Fatal error: {str(e)}'
            })
    
    def _run_single_backtest_safe(self, strategy_id, crypto, parameters,
                                  start_date, end_date, interval, use_daily_sampling):
        """
        Safely run a single backtest with error handling
        
        Returns:
            dict: Backtest result with success flag
        """
        try:
            result = self.backtest_service.run_backtest(
                strategy_id=strategy_id,
                crypto_id=crypto['id'],
                parameters=parameters,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                use_daily_sampling=use_daily_sampling
            )
            
            # Add crypto metadata
            result['crypto_id'] = crypto['id']
            result['symbol'] = crypto['symbol']
            result['name'] = crypto['name']
            result['success'] = True
            
            return result
            
        except Exception as e:
            return {
                'crypto_id': crypto['id'],
                'symbol': crypto['symbol'],
                'name': crypto['name'],
                'success': False,
                'error': str(e)
            }
    
    def _calculate_summary(self, results, total, successful, failed):
        """Calculate summary statistics from results"""
        if not results:
            return {
                'total_cryptocurrencies': total,
                'successful_backtests': successful,
                'failed_backtests': failed,
                'average_return': 0,
                'positive_returns_count': 0,
                'best_performing': None,
                'worst_performing': None
            }
        
        avg_return = sum(r['total_return'] for r in results) / len(results)
        best_crypto = max(results, key=lambda x: x['total_return'])
        worst_crypto = min(results, key=lambda x: x['total_return'])
        positive_returns = len([r for r in results if r['total_return'] > 0])
        
        # Calculate total winning and losing trades across all results
        total_winning_trades = sum(r.get('profitable_trades', 0) for r in results)
        total_losing_trades = sum(r.get('losing_trades', 0) for r in results)
        
        return {
            'total_cryptocurrencies': total,
            'successful_backtests': successful,
            'failed_backtests': failed,
            'average_return': round(avg_return, 2),
            'positive_returns_count': positive_returns,
            'total_winning_trades': total_winning_trades,
            'total_losing_trades': total_losing_trades,
            'best_performing': {
                'symbol': best_crypto['symbol'],
                'name': best_crypto['name'],
                'return': round(best_crypto['total_return'], 2)
            },
            'worst_performing': {
                'symbol': worst_crypto['symbol'],
                'name': worst_crypto['name'],
                'return': round(worst_crypto['total_return'], 2)
            }
        }
    
    def _format_sse(self, data):
        """
        Format data as Server-Sent Event
        
        Args:
            data: Dictionary to send
            
        Returns:
            str: Formatted SSE message
        """
        return f"data: {json.dumps(data)}\n\n"
