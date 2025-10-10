"""
Tests holdings storage operations and upsert logic.
"""

from datetime import datetime, timezone
from decimal import Decimal

from data.storage import upsert_holdings
from data.storage.db_context import _cursor_context

from data.models import Holdings

class TestHoldingsUpsert:
    """Test holdings upsert operations"""
    
    def test_upsert_holdings_timestamp_handling(self, temp_db):
        """Test holdings upsert preserves created_at, updates updated_at"""
            
            # Initial holdings
        holdings1 = Holdings(
            symbol="AAPL",
            quantity=Decimal('100'),
            break_even_price=Decimal('150.00'),
            total_cost=Decimal('15000.00'),
            notes="Initial position",
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        )
        
        # Store initial holdings
        upsert_holdings(temp_db, holdings1)
            
        # Updated holdings (same symbol = conflict)
        holdings2 = Holdings(
            symbol="AAPL",  # Same primary key
            quantity=Decimal('150'),  # Should update
            break_even_price=Decimal('148.00'),  # Should update
            total_cost=Decimal('22200.00'),  # Should update
            notes="Added more shares",  # Should update
            created_at=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),  # Should be ignored (preserve original)
            updated_at=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)   # Should update
        )
        
        # Upsert updated holdings
        upsert_holdings(temp_db, holdings2)
        
        # Verify record was updated properly
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*), quantity, break_even_price, total_cost, notes,
                        created_at_iso, updated_at_iso
                FROM holdings WHERE symbol = 'AAPL'
            """)
            count, qty, price, cost, notes, created, updated = cursor.fetchone()
            
            assert count == 1, f"Expected 1 record, got {count}"
            assert qty == "150", "quantity should be updated"
            assert price == "148.00", "break_even_price should be updated"
            assert cost == "22200.00", "total_cost should be updated"
            assert notes == "Added more shares", "notes should be updated"
            assert created == "2024-01-15T09:00:00Z", "created_at should be preserved from first insert"
            assert updated == "2024-01-15T12:00:00Z", "updated_at should be from update"
    
    def test_upsert_holdings_auto_timestamps(self, temp_db):
        """Test automatic timestamp generation when not provided"""
            
        # Holdings without timestamps
        holdings = Holdings(
            symbol="TSLA",
            quantity=Decimal('50'),
            break_even_price=Decimal('200.00'),
            total_cost=Decimal('10000.00'),
            notes="New position"
            # created_at and updated_at not provided
        )
        
        # Store holdings
        upsert_holdings(temp_db, holdings)
        
        # Verify timestamps were set automatically
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("""
                SELECT created_at_iso, updated_at_iso FROM holdings
                WHERE symbol = 'TSLA'
            """)
            created, updated = cursor.fetchone()
            
            # Both should be valid ISO timestamps
            assert created is not None
            assert updated is not None  
            assert "T" in created and "T" in updated
            assert created.endswith("Z") and updated.endswith("Z")
            # Should be approximately the same time
            assert created == updated