"""
End-to-end data roundtrip tests.
Tests complete data flow through storage and retrieval for all models,
validating field preservation, timezone handling, and cross-model consistency.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration]

from data.storage import (
    init_database, store_news_items, store_price_data,
    get_news_since, get_price_data_since, upsert_analysis_result,
    upsert_holdings, get_all_holdings, get_analysis_results
)
from data.models import (
    NewsItem, PriceData, AnalysisResult, Holdings,
    Session, Stance, AnalysisType
)


class TestDataRoundtrip:
    """Test complete end-to-end data roundtrip scenarios across all models"""
    
    def test_complete_data_roundtrip(self, temp_db):
        """
        Test complete data roundtrip for all models:
        1. Create instances of all data models with realistic test data
        2. Store them using storage functions
        3. Query them back using get functions
        4. Validate all field values are preserved exactly (especially Decimal precision)
        """
        # 1. CREATE REALISTIC TEST DATA
        test_timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        naive_timestamp = datetime(2024, 1, 15, 14, 45, 30)  # Will be converted to UTC
        
        # NewsItems with realistic symbols and boundary cases
        news_items = [
            NewsItem(
                symbol="AAPL",
                url="https://finance.yahoo.com/news/apple-earnings-report?utm_source=newsletter",
                headline="Apple Reports Strong Q1 Earnings, Stock Jumps",
                content="Apple Inc. reported stronger-than-expected quarterly earnings...",
                source="Yahoo Finance",
                published=test_timestamp
            ),
            NewsItem(
                symbol="TSLA",
                url="https://reuters.com/business/tesla-production-update",
                headline="Tesla Increases Production Guidance for 2024",
                content=None,  # Test None content
                source="Reuters",
                published=naive_timestamp  # Test timezone conversion
            ),
            NewsItem(
                symbol="SPY",
                url="https://bloomberg.com/markets/etf-flows",
                headline="SPY ETF Sees Record Inflows Amid Market Rally",
                content="",  # Test empty content
                source="Bloomberg",
                published=test_timestamp
            )
        ]
        
        # PriceData with boundary financial values and all session types
        price_data = [
            PriceData(
                symbol="AAPL",
                timestamp=test_timestamp,
                price=Decimal('189.7500'),  # Realistic stock price
                volume=1234567,
                session=Session.REG
            ),
            PriceData(
                symbol="TSLA", 
                timestamp=naive_timestamp,  # Test timezone conversion
                price=Decimal('0.0001'),    # Boundary value - very small price
                volume=0,  # Test zero volume
                session=Session.PRE
            ),
            PriceData(
                symbol="SPY",
                timestamp=test_timestamp,
                price=Decimal('999999.99'),  # Boundary value - very large price
                volume=None,  # Test None volume
                session=Session.POST
            )
        ]
        
        # AnalysisResults with all enum combinations
        analysis_results = [
            AnalysisResult(
                symbol="AAPL",
                analysis_type=AnalysisType.NEWS_ANALYSIS,
                model_name="gpt-4o",
                stance=Stance.BULL,
                confidence_score=0.8500,  # Test specific precision
                last_updated=test_timestamp,
                result_json='{"sentiment": "positive", "key_factors": ["strong earnings", "guidance beat"]}',
                created_at=naive_timestamp  # Test timezone conversion
            ),
            AnalysisResult(
                symbol="TSLA",
                analysis_type=AnalysisType.SENTIMENT_ANALYSIS,
                model_name="claude-3-5-sonnet",
                stance=Stance.NEUTRAL,
                confidence_score=0.0001,  # Boundary value - minimum confidence
                last_updated=naive_timestamp,
                result_json='{"sentiment": "neutral", "volatility": "high"}'
                # created_at not provided - test auto-generation
            ),
            AnalysisResult(
                symbol="SPY",
                analysis_type=AnalysisType.HEAD_TRADER,
                model_name="gpt-4-turbo",
                stance=Stance.BEAR,
                confidence_score=0.9999,  # Boundary value - near maximum confidence
                last_updated=test_timestamp,
                result_json='{"recommendation": "sell", "risk_level": "moderate"}',
                created_at=test_timestamp
            )
        ]
        
        # Holdings with boundary financial values and precision testing
        holdings_list = [
            Holdings(
                symbol="AAPL",
                quantity=Decimal('100.500000'),  # Test precision preservation
                break_even_price=Decimal('189.7500'),
                total_cost=Decimal('18975.00'),
                notes="Long-term position",
                created_at=test_timestamp,
                updated_at=test_timestamp
            ),
            Holdings(
                symbol="TSLA",
                quantity=Decimal('0.000001'),  # Boundary value - very small quantity
                break_even_price=Decimal('0.000001'),  # Boundary value - very small price
                total_cost=Decimal('0.000000000001'),  # Boundary value - tiny cost
                notes="Test fractional shares",
                created_at=naive_timestamp,  # Test timezone conversion
                updated_at=naive_timestamp
            ),
            Holdings(
                symbol="SPY",
                quantity=Decimal('999999.999999'),  # Boundary value - large quantity
                break_even_price=Decimal('999999.99'),  # Boundary value - large price
                total_cost=Decimal('999999999998.99'),  # Boundary value - large cost
                notes="  Massive position  ",  # Test note trimming
                # Test auto-timestamps by not providing created_at/updated_at
            )
        ]
        
        # 2. STORE ALL DATA USING STORAGE FUNCTIONS
        store_news_items(temp_db, news_items)
        store_price_data(temp_db, price_data)
        
        for result in analysis_results:
            upsert_analysis_result(temp_db, result)
            
        for holdings in holdings_list:
            upsert_holdings(temp_db, holdings)
        
        # 3. QUERY ALL DATA BACK USING GET FUNCTIONS
        retrieved_news = get_news_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc))
        retrieved_prices = get_price_data_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc))
        retrieved_analysis = get_analysis_results(temp_db)
        retrieved_holdings = get_all_holdings(temp_db)
        
        # 4. VALIDATE ALL FIELD VALUES ARE PRESERVED EXACTLY
        
        # Verify NewsItems
        assert len(retrieved_news) == 3, f"Expected 3 news items, got {len(retrieved_news)}"
        
        # Find AAPL news item
        aapl_news = next(item for item in retrieved_news if item['symbol'] == 'AAPL')
        assert aapl_news['url'] == "https://finance.yahoo.com/news/apple-earnings-report"  # URL normalized (tracking removed)
        assert aapl_news['headline'] == "Apple Reports Strong Q1 Earnings, Stock Jumps"
        assert aapl_news['content'] == "Apple Inc. reported stronger-than-expected quarterly earnings..."
        assert aapl_news['source'] == "Yahoo Finance"
        assert aapl_news['published_iso'] == "2024-01-15T10:30:45Z"
        
        # Find TSLA news item - test timezone conversion and None content
        tsla_news = next(item for item in retrieved_news if item['symbol'] == 'TSLA')
        assert tsla_news['content'] is None  # None preserved
        assert tsla_news['published_iso'] == "2024-01-15T14:45:30Z"  # Naive converted to UTC
        
        # Find SPY news item - test empty content
        spy_news = next(item for item in retrieved_news if item['symbol'] == 'SPY')
        assert spy_news['content'] == ""  # Empty string preserved
        
        # Verify PriceData with Decimal precision
        assert len(retrieved_prices) == 3, f"Expected 3 price data items, got {len(retrieved_prices)}"
        
        # Find AAPL price data
        aapl_price = next(item for item in retrieved_prices if item['symbol'] == 'AAPL')
        assert aapl_price['price'] == "189.7500"  # Decimal precision preserved as TEXT
        assert aapl_price['volume'] == 1234567
        assert aapl_price['session'] == "REG"
        assert aapl_price['timestamp_iso'] == "2024-01-15T10:30:45Z"
        
        # Find TSLA price data - test boundary values and timezone
        tsla_price = next(item for item in retrieved_prices if item['symbol'] == 'TSLA')
        assert tsla_price['price'] == "0.0001"  # Boundary value preserved
        assert tsla_price['volume'] == 0  # Zero volume preserved
        assert tsla_price['session'] == "PRE"
        assert tsla_price['timestamp_iso'] == "2024-01-15T14:45:30Z"  # Naive converted to UTC
        
        # Find SPY price data - test large boundary value and None volume
        spy_price = next(item for item in retrieved_prices if item['symbol'] == 'SPY')
        assert spy_price['price'] == "999999.99"  # Large boundary value preserved
        assert spy_price['volume'] is None  # None volume preserved
        assert spy_price['session'] == "POST"
        
        # Verify AnalysisResults
        assert len(retrieved_analysis) == 3, f"Expected 3 analysis results, got {len(retrieved_analysis)}"
        
        # Find AAPL analysis
        aapl_analysis = next(item for item in retrieved_analysis if item['symbol'] == 'AAPL')
        assert aapl_analysis['analysis_type'] == "news_analysis"
        assert aapl_analysis['model_name'] == "gpt-4o"
        assert aapl_analysis['stance'] == "BULL"
        assert aapl_analysis['confidence_score'] == 0.8500  # Exact precision preserved
        assert aapl_analysis['last_updated_iso'] == "2024-01-15T10:30:45Z"
        assert aapl_analysis['result_json'] == '{"sentiment": "positive", "key_factors": ["strong earnings", "guidance beat"]}'
        assert aapl_analysis['created_at_iso'] == "2024-01-15T14:45:30Z"  # Timezone conversion
        
        # Find TSLA analysis - test boundary confidence and auto-created_at
        tsla_analysis = next(item for item in retrieved_analysis if item['symbol'] == 'TSLA')
        assert tsla_analysis['confidence_score'] == 0.0001  # Boundary value preserved
        assert tsla_analysis['stance'] == "NEUTRAL"
        assert tsla_analysis['created_at_iso'] is not None  # Auto-generated
        assert "T" in tsla_analysis['created_at_iso'] and tsla_analysis['created_at_iso'].endswith("Z")
        
        # Find SPY analysis - test near-max confidence
        spy_analysis = next(item for item in retrieved_analysis if item['symbol'] == 'SPY')
        assert spy_analysis['confidence_score'] == 0.9999  # Near-max boundary preserved
        assert spy_analysis['stance'] == "BEAR"
        
        # Verify Holdings with Decimal precision
        assert len(retrieved_holdings) == 3, f"Expected 3 holdings, got {len(retrieved_holdings)}"
        
        # Find AAPL holdings
        aapl_holdings = next(item for item in retrieved_holdings if item['symbol'] == 'AAPL')
        assert aapl_holdings['quantity'] == "100.500000"  # Full precision preserved
        assert aapl_holdings['break_even_price'] == "189.7500"
        assert aapl_holdings['total_cost'] == "18975.00"
        assert aapl_holdings['notes'] == "Long-term position"
        assert aapl_holdings['created_at_iso'] == "2024-01-15T10:30:45Z"
        assert aapl_holdings['updated_at_iso'] == "2024-01-15T10:30:45Z"
        
        # Find TSLA holdings - test boundary values
        tsla_holdings = next(item for item in retrieved_holdings if item['symbol'] == 'TSLA')
        assert tsla_holdings['quantity'] == "0.000001"  # Tiny quantity preserved
        assert tsla_holdings['break_even_price'] == "0.000001"  # Tiny price preserved
        # Scientific notation may be used for very small numbers
        assert tsla_holdings['total_cost'] in ["0.000000000001", "1E-12"]  # Tiny cost preserved (both representations valid)
        assert tsla_holdings['notes'] == "Test fractional shares"
        assert tsla_holdings['created_at_iso'] == "2024-01-15T14:45:30Z"  # Timezone conversion
        assert tsla_holdings['updated_at_iso'] == "2024-01-15T14:45:30Z"
        
        # Find SPY holdings - test large boundary values and auto-timestamps
        spy_holdings = next(item for item in retrieved_holdings if item['symbol'] == 'SPY')
        assert spy_holdings['quantity'] == "999999.999999"  # Large quantity preserved
        assert spy_holdings['break_even_price'] == "999999.99"  # Large price preserved
        assert spy_holdings['total_cost'] == "999999999998.99"  # Large cost preserved
        assert spy_holdings['notes'] == "Massive position"  # Trimmed
        assert spy_holdings['created_at_iso'] is not None  # Auto-generated
        assert spy_holdings['updated_at_iso'] is not None  # Auto-generated
        assert "T" in spy_holdings['created_at_iso'] and spy_holdings['created_at_iso'].endswith("Z")
        assert "T" in spy_holdings['updated_at_iso'] and spy_holdings['updated_at_iso'].endswith("Z")
    
    def test_cross_model_data_consistency(self, temp_db):
        """
        Test data consistency across models for the same symbols.
        Verify that data stored for the same symbol maintains consistency.
        """
        # Store data for AAPL across all models
        symbol = "AAPL"
        test_time = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        
        # Store news
        news = [NewsItem(
            symbol=symbol,
            url="https://example.com/aapl-news",
            headline="AAPL News",
            source="Test Source", 
            published=test_time
        )]
        store_news_items(temp_db, news)
        
        # Store price data
        prices = [PriceData(
            symbol=symbol,
            timestamp=test_time,
            price=Decimal('150.00'),
            volume=1000000,
            session=Session.REG
        )]
        store_price_data(temp_db, prices)
        
        # Store analysis
        analysis = AnalysisResult(
            symbol=symbol,
            analysis_type=AnalysisType.NEWS_ANALYSIS,
            model_name="test-model",
            stance=Stance.BULL,
            confidence_score=0.85,
            last_updated=test_time,
            result_json='{"test": "data"}'
        )
        upsert_analysis_result(temp_db, analysis)
        
        # Store holdings
        holdings = Holdings(
            symbol=symbol,
            quantity=Decimal('100'),
            break_even_price=Decimal('150.00'),
            total_cost=Decimal('15000.00'),
            created_at=test_time,
            updated_at=test_time
        )
        upsert_holdings(temp_db, holdings)
        
        # Query all data for AAPL
        news_results = get_news_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc))
        price_results = get_price_data_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc))
        analysis_results = get_analysis_results(temp_db, symbol=symbol)
        holdings_results = get_all_holdings(temp_db)
        
        # Verify all results are for AAPL and contain expected data
        assert len(news_results) == 1 and news_results[0]['symbol'] == symbol
        assert len(price_results) == 1 and price_results[0]['symbol'] == symbol  
        assert len(analysis_results) == 1 and analysis_results[0]['symbol'] == symbol
        assert len(holdings_results) == 1 and holdings_results[0]['symbol'] == symbol
        
        # Verify specific values match what we stored
        assert news_results[0]['headline'] == "AAPL News"
        assert price_results[0]['price'] == "150.00"
        assert analysis_results[0]['stance'] == "BULL"
        assert holdings_results[0]['quantity'] == "100"

    def test_upsert_invariants(self, temp_db):
        """
        Test that upsert operations preserve created_at but update other timestamps.
        
        This test validates:
        1. Holdings upsert preserves created_at, advances updated_at
        2. AnalysisResult upsert preserves created_at, advances last_updated
        """
        # Set up initial timestamps
        initial_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        update_time = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        
        # TEST HOLDINGS UPSERT BEHAVIOR
        
        # 1. Create and store initial Holdings
        initial_holdings = Holdings(
            symbol="TEST",
            quantity=Decimal('100'),
            break_even_price=Decimal('50.00'),
            total_cost=Decimal('5000.00'),
            notes="Initial position",
            created_at=initial_time,
            updated_at=initial_time
        )
        upsert_holdings(temp_db, initial_holdings)
        
        # Verify initial storage
        holdings_results = [h for h in get_all_holdings(temp_db) if h['symbol'] == 'TEST']
        assert len(holdings_results) == 1
        initial_stored = holdings_results[0]
        assert initial_stored['created_at_iso'] == "2024-01-15T10:00:00Z"
        assert initial_stored['updated_at_iso'] == "2024-01-15T10:00:00Z"
        assert initial_stored['quantity'] == "100"
        assert initial_stored['notes'] == "Initial position"
        
        # 2. Update the Holdings (same symbol, different values)
        updated_holdings = Holdings(
            symbol="TEST",  # Same symbol - triggers upsert update
            quantity=Decimal('150'),  # Changed
            break_even_price=Decimal('45.00'),  # Changed  
            total_cost=Decimal('6750.00'),  # Changed
            notes="Updated position",  # Changed
            created_at=update_time,  # This should be IGNORED (preserve original)
            updated_at=update_time   # This should be updated
        )
        upsert_holdings(temp_db, updated_holdings)
        
        # 3. Verify upsert behavior
        holdings_results = [h for h in get_all_holdings(temp_db) if h['symbol'] == 'TEST']
        assert len(holdings_results) == 1, "Should still be only one record after upsert"
        
        updated_stored = holdings_results[0]
        # created_at should be PRESERVED (not changed to update_time)
        assert updated_stored['created_at_iso'] == "2024-01-15T10:00:00Z", "created_at should be preserved during upsert"
        # updated_at should be ADVANCED (changed to update_time)  
        assert updated_stored['updated_at_iso'] == "2024-01-15T11:00:00Z", "updated_at should advance during upsert"
        # Other fields should be updated
        assert updated_stored['quantity'] == "150", "quantity should be updated"
        assert updated_stored['break_even_price'] == "45.00", "break_even_price should be updated"  
        assert updated_stored['total_cost'] == "6750.00", "total_cost should be updated"
        assert updated_stored['notes'] == "Updated position", "notes should be updated"
        
        # TEST ANALYSIS RESULT UPSERT BEHAVIOR
        
        # 1. Create and store initial AnalysisResult
        initial_analysis = AnalysisResult(
            symbol="TEST",
            analysis_type=AnalysisType.NEWS_ANALYSIS,
            model_name="test-model",
            stance=Stance.BULL,
            confidence_score=0.8,
            last_updated=initial_time,
            result_json='{"initial": "analysis"}',
            created_at=initial_time
        )
        upsert_analysis_result(temp_db, initial_analysis)
        
        # Verify initial storage
        analysis_results = get_analysis_results(temp_db, "TEST")
        assert len(analysis_results) == 1
        initial_analysis_stored = analysis_results[0]
        assert initial_analysis_stored['created_at_iso'] == "2024-01-15T10:00:00Z"
        assert initial_analysis_stored['last_updated_iso'] == "2024-01-15T10:00:00Z"
        assert initial_analysis_stored['stance'] == "BULL"
        assert initial_analysis_stored['confidence_score'] == 0.8
        
        # 2. Update the AnalysisResult (same symbol+analysis_type, different values)
        updated_analysis = AnalysisResult(
            symbol="TEST",  # Same symbol
            analysis_type=AnalysisType.NEWS_ANALYSIS,  # Same analysis_type - triggers upsert update
            model_name="updated-model",  # Changed
            stance=Stance.BEAR,  # Changed
            confidence_score=0.6,  # Changed
            last_updated=update_time,  # This should be updated
            result_json='{"updated": "analysis"}',  # Changed
            created_at=update_time  # This should be IGNORED (preserve original)
        )
        upsert_analysis_result(temp_db, updated_analysis)
        
        # 3. Verify upsert behavior
        analysis_results = get_analysis_results(temp_db, "TEST")
        assert len(analysis_results) == 1, "Should still be only one record after upsert"
        
        updated_analysis_stored = analysis_results[0]
        # created_at should be PRESERVED (not changed to update_time)
        assert updated_analysis_stored['created_at_iso'] == "2024-01-15T10:00:00Z", "created_at should be preserved during upsert"
        # last_updated should be ADVANCED (changed to update_time)
        assert updated_analysis_stored['last_updated_iso'] == "2024-01-15T11:00:00Z", "last_updated should advance during upsert"
        # Other fields should be updated
        assert updated_analysis_stored['model_name'] == "updated-model", "model_name should be updated"
        assert updated_analysis_stored['stance'] == "BEAR", "stance should be updated"
        assert updated_analysis_stored['confidence_score'] == 0.6, "confidence_score should be updated"
        assert updated_analysis_stored['result_json'] == '{"updated": "analysis"}', "result_json should be updated"

    def test_duplicate_price_prevention(self, temp_db):
        """
        Test that duplicate price data (same symbol + timestamp) is prevented by INSERT OR IGNORE.
        
        This test validates:
        1. First price data is stored successfully
        2. Second price data with same symbol+timestamp is ignored
        3. Only the first price data is preserved
        4. Different timestamps for same symbol are stored normally
        """
        test_timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        different_timestamp = datetime(2024, 1, 15, 14, 31, 0, tzinfo=timezone.utc)
        
        # 1. Store first price data
        first_price = [PriceData(
            symbol="DUP_TEST",
            timestamp=test_timestamp,
            price=Decimal('100.00'),
            volume=1000,
            session=Session.REG
        )]
        store_price_data(temp_db, first_price)
        
        # Verify first price is stored
        price_results = [p for p in get_price_data_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc)) 
                        if p['symbol'] == 'DUP_TEST']
        assert len(price_results) == 1, "First price should be stored"
        stored_price = price_results[0]
        assert stored_price['price'] == "100.00", "First price should be 100.00"
        assert stored_price['volume'] == 1000, "First volume should be 1000"
        assert stored_price['timestamp_iso'] == "2024-01-15T14:30:00Z", "Timestamp should match"
        
        # 2. Attempt to store duplicate price data (same symbol + timestamp, different values)
        duplicate_price = [PriceData(
            symbol="DUP_TEST",  # Same symbol
            timestamp=test_timestamp,  # Same timestamp - should trigger duplicate key
            price=Decimal('200.00'),  # Different price (should be ignored)
            volume=2000,  # Different volume (should be ignored)
            session=Session.POST  # Different session (should be ignored)
        )]
        store_price_data(temp_db, duplicate_price)
        
        # 3. Verify duplicate was ignored - still only one record with original values
        price_results = [p for p in get_price_data_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc)) 
                        if p['symbol'] == 'DUP_TEST']
        assert len(price_results) == 1, "Should still be only one price record after duplicate attempt"
        
        preserved_price = price_results[0]
        # Original values should be preserved (duplicate ignored)
        assert preserved_price['price'] == "100.00", "Original price should be preserved (duplicate ignored)"
        assert preserved_price['volume'] == 1000, "Original volume should be preserved (duplicate ignored)"
        assert preserved_price['session'] == "REG", "Original session should be preserved (duplicate ignored)"
        assert preserved_price['timestamp_iso'] == "2024-01-15T14:30:00Z", "Original timestamp should be preserved"
        
        # 4. Verify different timestamp for same symbol IS stored normally
        different_time_price = [PriceData(
            symbol="DUP_TEST",  # Same symbol
            timestamp=different_timestamp,  # DIFFERENT timestamp - should be stored
            price=Decimal('150.00'),  # Different price
            volume=1500,  # Different volume  
            session=Session.PRE  # Different session
        )]
        store_price_data(temp_db, different_time_price)
        
        # Should now have 2 records for the symbol
        price_results = [p for p in get_price_data_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc)) 
                        if p['symbol'] == 'DUP_TEST']
        assert len(price_results) == 2, "Should now have 2 price records for different timestamps"
        
        # Sort by timestamp to verify both records
        price_results.sort(key=lambda x: x['timestamp_iso'])
        
        first_record = price_results[0]  # Earlier timestamp
        assert first_record['timestamp_iso'] == "2024-01-15T14:30:00Z"
        assert first_record['price'] == "100.00"
        assert first_record['volume'] == 1000
        assert first_record['session'] == "REG"
        
        second_record = price_results[1]  # Later timestamp
        assert second_record['timestamp_iso'] == "2024-01-15T14:31:00Z"
        assert second_record['price'] == "150.00"  
        assert second_record['volume'] == 1500
        assert second_record['session'] == "PRE"
        
        # 5. Test duplicate prevention across different symbols (should NOT prevent storage)
        different_symbol_price = [PriceData(
            symbol="DIFFERENT_SYMBOL",  # DIFFERENT symbol
            timestamp=test_timestamp,  # Same timestamp as first test - should be allowed
            price=Decimal('300.00'),
            volume=3000,
            session=Session.POST
        )]
        store_price_data(temp_db, different_symbol_price)
        
        # Should now have 3 total records (2 for DUP_TEST, 1 for DIFFERENT_SYMBOL)
        all_price_results = get_price_data_since(temp_db, datetime(2024, 1, 1, tzinfo=timezone.utc))
        dup_test_results = [p for p in all_price_results if p['symbol'] == 'DUP_TEST']
        different_symbol_results = [p for p in all_price_results if p['symbol'] == 'DIFFERENT_SYMBOL']
        
        assert len(dup_test_results) == 2, "Should still have 2 records for DUP_TEST"
        assert len(different_symbol_results) == 1, "Should have 1 record for DIFFERENT_SYMBOL"
        
        # Verify the different symbol record was stored correctly
        diff_symbol_record = different_symbol_results[0]
        assert diff_symbol_record['price'] == "300.00"
        assert diff_symbol_record['volume'] == 3000
        assert diff_symbol_record['session'] == "POST"
        assert diff_symbol_record['timestamp_iso'] == "2024-01-15T14:30:00Z"