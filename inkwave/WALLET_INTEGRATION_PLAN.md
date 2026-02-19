# Wallet Integration with Reading Platform - Implementation Plan

**Date**: 2025-11-12
**Status**: 📋 **READY TO IMPLEMENT**
**Priority**: 🔴 **CRITICAL FOR PRODUCTION**

---

## Executive Summary

This document outlines the complete integration of the wallet/credits system with InkWave's reading platform, enabling:
1. **Automated credit charging** during listening/reading
2. **Per-book revenue tracking** for each title in the library
3. **Total platform revenue** calculations and reporting
4. **Admin revenue dashboard** for financial insights

---

## Current State Analysis

### ✅ Already Implemented:
1. **Wallet Service** (`/api/v1/wallet/*`)
   - Balance viewing
   - Transaction history
   - Top-up functionality
   - Pricing model ($0.10/minute)

2. **Analytics Service** (`services/analytics_service.py`)
   - Book-level analytics (listening time, AI interactions)
   - User listening stats
   - Popular books ranking
   - **⚠️ Uses wallet transaction metadata**

3. **Reading Sessions** (`models/session.py`)
   - Progress tracking
   - Time spent tracking
   - Bookmark management

4. **Audio Generation** (`api/routes/reading.py:333`)
   - **📍 TODO comment for wallet charging**
   - TTS generation
   - Audio streaming

### ⚠️ Missing:
1. **No automated charging** - Users get unlimited free usage
2. **No pre-flight balance checks** - Can listen without credits
3. **No revenue totals calculation** - Analytics exist but no revenue summary
4. **No admin revenue dashboard** - Cannot view platform earnings
5. **No per-book revenue display** - Cannot see which books make money

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   USER READING FLOW                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. User clicks "Listen" on book                            │
│     ↓ Check Balance                                         │
│  2. Verify user has sufficient credits                      │
│     ↓ Balance >= $0.10? (1 minute minimum)                  │
│  3. Start audio playback                                    │
│     ↓ Every 10 seconds                                      │
│  4. Charge for listening time (batch charging)              │
│     ↓ Update session                                        │
│  5. Track time in reading_sessions collection               │
│     ↓ Record transaction                                    │
│  6. Store transaction with book_id metadata                 │
│     ↓ Update analytics                                      │
│  7. Analytics aggregates revenue by book                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 ADMIN REVENUE DASHBOARD                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  • Total Platform Revenue (all time, monthly, weekly)       │
│  • Top Earning Books (ranked by revenue)                    │
│  • Revenue by Service (listening vs Q&A vs TTS)             │
│  • User Spending Distribution                               │
│  • Revenue Growth Charts                                    │
│  • Top Paying Users                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Automated Credit Charging (Critical)
**Goal**: Charge users automatically during listening
**Timeline**: 2-3 days
**Priority**: 🔴 Critical

#### 1.1 Pre-Flight Balance Check
**File**: `backend/app/api/routes/reading.py`

Add balance check before audio generation:

```python
@router.get("/chunks/{book_id}/{chunk_index}/audio")
async def get_chunk_audio(
    book_id: str,
    chunk_index: int,
    voice: str = "alloy",
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service),
    tts_service: TTSService = Depends(get_tts_service),
    wallet_service: InkWaveWalletService = Depends(get_wallet_service)  # NEW
):
    """Get or generate audio for a book chunk (WITH WALLET CHARGING)."""

    user_id = current_user.user_id

    # 🔹 NEW: Check balance before generating audio
    balance = await wallet_service.get_balance(user_id)

    minimum_balance = Decimal("0.10")  # $0.10 = 1 minute
    if not balance or balance < minimum_balance:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "insufficient_balance",
                "message": "Insufficient credits to play audio. Please top up your wallet.",
                "current_balance": float(balance) if balance else 0.0,
                "required_balance": float(minimum_balance),
                "topup_url": "/wallet"
            }
        )

    # Get chunk and generate audio...
    chunk = await reading_service.get_chunk(book_id, chunk_index)

    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    # Estimate audio duration (approx 150 words per minute)
    word_count = len(chunk.text.split())
    estimated_duration_minutes = word_count / 150.0

    # Calculate cost
    cost = Decimal(str(estimated_duration_minutes)) * Decimal("0.10")

    # Generate audio
    text = chunk.text_optimized or chunk.text
    text = tts_service.optimize_text_for_tts(text)

    audio_data = await tts_service.generate_chunk_audio(
        book_id=book_id,
        chunk_index=chunk_index,
        text=text,
        voice=voice
    )

    # 🔹 NEW: Charge wallet AFTER successful generation
    transaction = await wallet_service.charge_listening_time(
        user_id=user_id,
        book_id=book_id,
        duration_minutes=estimated_duration_minutes,
        book_title=chunk.title or book_id
    )

    if not transaction:
        # Charging failed (shouldn't happen after balance check, but handle it)
        logger.error(f"Failed to charge user {user_id} for listening")
        # Still return audio but log the error

    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"inline; filename=chunk_{chunk_index}.mp3",
            "X-Credits-Charged": str(float(cost)),  # Inform frontend
            "X-Estimated-Duration": str(estimated_duration_minutes)
        }
    )
```

#### 1.2 Batch Charging for Long Sessions
**File**: `backend/app/services/reading_service.py`

Add method to charge for accumulated listening time:

```python
async def charge_session_listening_time(
    self,
    session_id: str,
    user_id: str,
    minutes_since_last_charge: float
) -> bool:
    """
    Charge user for accumulated listening time in a session.

    Called periodically (every 10 seconds) from frontend to batch charges.

    Args:
        session_id: Reading session ID
        user_id: User ID
        minutes_since_last_charge: Minutes to charge for

    Returns:
        True if charged successfully, False if insufficient balance
    """
    if minutes_since_last_charge <= 0:
        return True

    # Get session to get book details
    session = await self.get_session(session_id, user_id)
    if not session:
        return False

    # Get wallet service
    from app.services.wallet_service import get_wallet_service
    wallet_service = await get_wallet_service()

    # Get book title for better transaction description
    book = await self.db.books.find_one({"book_id": session.book_id})
    book_title = book.get("title") if book else session.book_id

    # Charge wallet
    transaction = await wallet_service.charge_listening_time(
        user_id=user_id,
        book_id=session.book_id,
        duration_minutes=minutes_since_last_charge,
        book_title=book_title
    )

    if not transaction:
        # Insufficient balance
        return False

    # Update session time spent
    await self.update_progress(
        session_id=session_id,
        user_id=user_id,
        update=ReadingSessionUpdate(
            total_time_spent_minutes=session.total_time_spent_minutes + int(minutes_since_last_charge)
        )
    )

    return True
```

#### 1.3 Frontend Integration
**File**: `frontend/src/components/AudioPlayer.tsx`

Add periodic charging:

```typescript
// Inside audio player component
const [chargingTimer, setChargingTimer] = useState<NodeJS.Timeout | null>(null);
const [accumulatedMinutes, setAccumulatedMinutes] = useState(0);
const [lastChargeTime, setLastChargeTime] = useState(Date.now());

// Start charging timer when playback starts
useEffect(() => {
  if (isPlaying && sessionId) {
    const timer = setInterval(async () => {
      const now = Date.now();
      const minutesSinceLastCharge = (now - lastChargeTime) / 1000 / 60;

      if (minutesSinceLastCharge >= 0.16) {  // Charge every 10 seconds
        try {
          const response = await api.reading.chargeListeningTime(
            sessionId,
            minutesSinceLastCharge
          );

          if (response.data.success) {
            setLastChargeTime(now);
            setAccumulatedMinutes(prev => prev + minutesSinceLastCharge);
          } else {
            // Insufficient balance - pause playback
            pause();
            toast.error('Insufficient credits. Please top up to continue listening.');
            navigate('/wallet');
          }
        } catch (error) {
          console.error('Failed to charge for listening time:', error);
        }
      }
    }, 10000);  // Check every 10 seconds

    setChargingTimer(timer);

    return () => {
      if (timer) clearInterval(timer);
    };
  }
}, [isPlaying, sessionId]);
```

---

### Phase 2: Revenue Tracking & Reporting (High Priority)
**Goal**: Track and display total revenue by book and platform-wide
**Timeline**: 2 days
**Priority**: 🟡 High

#### 2.1 Enhanced Revenue Analytics Service
**File**: `backend/app/services/revenue_service.py` (NEW)

```python
"""
Revenue Analytics Service for InkWave.

Calculates total revenue, per-book revenue, and revenue trends.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class RevenueService:
    """Service for revenue calculations and reporting."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize revenue service."""
        self.db = db
        self.transactions = db.transactions  # Shared wallet transactions

    async def get_total_platform_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate total platform revenue.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary with total revenue breakdown
        """
        if not start_date:
            start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        pipeline = [
            {
                "$match": {
                    "type": "debit",  # Only debits (money spent by users)
                    "status": "completed",
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "metadata.service": {"$in": ["inkwave_listening", "inkwave_ai"]}
                }
            },
            {
                "$group": {
                    "_id": "$metadata.service",
                    "total_revenue": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1}
                }
            }
        ]

        results = await self.transactions.aggregate(pipeline).to_list(length=100)

        # Calculate totals
        listening_revenue = Decimal("0.00")
        ai_revenue = Decimal("0.00")
        listening_transactions = 0
        ai_transactions = 0

        for result in results:
            service = result["_id"]
            revenue = abs(Decimal(str(result["total_revenue"])))
            count = result["transaction_count"]

            if service == "inkwave_listening":
                listening_revenue = revenue
                listening_transactions = count
            elif service == "inkwave_ai":
                ai_revenue = revenue
                ai_transactions = count

        total_revenue = listening_revenue + ai_revenue
        total_transactions = listening_transactions + ai_transactions

        return {
            "total_revenue": float(total_revenue),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "breakdown": {
                "listening": {
                    "revenue": float(listening_revenue),
                    "transactions": listening_transactions,
                    "percentage": float(listening_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
                },
                "ai_interactions": {
                    "revenue": float(ai_revenue),
                    "transactions": ai_transactions,
                    "percentage": float(ai_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
                }
            },
            "average_transaction_value": float(total_revenue / total_transactions) if total_transactions > 0 else 0.0
        }

    async def get_revenue_by_book(
        self,
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get revenue breakdown by book (top earners).

        Args:
            limit: Number of books to return
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of books with revenue data
        """
        if not start_date:
            start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        pipeline = [
            {
                "$match": {
                    "type": "debit",
                    "status": "completed",
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "metadata.service": {"$in": ["inkwave_listening", "inkwave_ai"]},
                    "metadata.book_id": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$metadata.book_id",
                    "total_revenue": {"$sum": "$amount"},
                    "listening_revenue": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$metadata.service", "inkwave_listening"]},
                                "$amount",
                                0
                            ]
                        }
                    },
                    "ai_revenue": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$metadata.service", "inkwave_ai"]},
                                "$amount",
                                0
                            ]
                        }
                    },
                    "unique_users": {"$addToSet": "$wallet_id"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "book_id": "$_id",
                    "total_revenue": {"$abs": "$total_revenue"},
                    "listening_revenue": {"$abs": "$listening_revenue"},
                    "ai_revenue": {"$abs": "$ai_revenue"},
                    "unique_users": {"$size": "$unique_users"},
                    "transaction_count": 1
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$limit": limit
            }
        ]

        results = await self.transactions.aggregate(pipeline).to_list(length=limit)

        # Enrich with book details
        enriched_results = []
        for result in results:
            book_id = result["book_id"]

            # Get book title from books collection
            book = await self.db.books.find_one({"book_id": book_id})

            enriched_results.append({
                "book_id": book_id,
                "title": book.get("title") if book else "Unknown",
                "author": book.get("author") if book else "Unknown",
                "total_revenue": float(result["total_revenue"]),
                "listening_revenue": float(result["listening_revenue"]),
                "ai_revenue": float(result["ai_revenue"]),
                "unique_users": result["unique_users"],
                "transaction_count": result["transaction_count"],
                "average_revenue_per_user": float(result["total_revenue"] / result["unique_users"]) if result["unique_users"] > 0 else 0.0
            })

        return enriched_results

    async def get_revenue_trends(
        self,
        days: int = 30,
        granularity: str = "daily"  # daily, weekly, monthly
    ) -> Dict[str, Any]:
        """
        Get revenue trends over time.

        Args:
            days: Number of days to look back
            granularity: daily, weekly, or monthly

        Returns:
            Dictionary with time-series revenue data
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Determine date grouping format
        if granularity == "daily":
            date_format = "%Y-%m-%d"
        elif granularity == "weekly":
            date_format = "%Y-W%U"
        else:  # monthly
            date_format = "%Y-%m"

        pipeline = [
            {
                "$match": {
                    "type": "debit",
                    "status": "completed",
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "metadata.service": {"$in": ["inkwave_listening", "inkwave_ai"]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                        "service": "$metadata.service"
                    },
                    "revenue": {"$sum": "$amount"}
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "listening_revenue": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$_id.service", "inkwave_listening"]},
                                {"$abs": "$revenue"},
                                0
                            ]
                        }
                    },
                    "ai_revenue": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$_id.service", "inkwave_ai"]},
                                {"$abs": "$revenue"},
                                0
                            ]
                        }
                    }
                }
            },
            {
                "$project": {
                    "date": "$_id",
                    "listening_revenue": 1,
                    "ai_revenue": 1,
                    "total_revenue": {"$add": ["$listening_revenue", "$ai_revenue"]}
                }
            },
            {
                "$sort": {"date": 1}
            }
        ]

        results = await self.transactions.aggregate(pipeline).to_list(length=1000)

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
                "granularity": granularity
            },
            "data": [
                {
                    "date": r["date"],
                    "total_revenue": float(r["total_revenue"]),
                    "listening_revenue": float(r["listening_revenue"]),
                    "ai_revenue": float(r["ai_revenue"])
                }
                for r in results
            ]
        }
```

#### 2.2 Admin Revenue API Endpoints
**File**: `backend/app/api/routes/admin.py` (add to existing)

```python
@router.get("/revenue/total", summary="Get total platform revenue")
async def get_total_revenue(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin_user),  # Admin only!
    revenue_service: RevenueService = Depends(get_revenue_service)
):
    """Get total platform revenue (admin only)."""
    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    revenue_data = await revenue_service.get_total_platform_revenue(
        start_date=start_dt,
        end_date=end_dt
    )

    return revenue_data


@router.get("/revenue/by-book", summary="Get revenue by book")
async def get_revenue_by_book(
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin_user),
    revenue_service: RevenueService = Depends(get_revenue_service)
):
    """Get revenue breakdown by book (admin only)."""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    books = await revenue_service.get_revenue_by_book(
        limit=limit,
        start_date=start_dt,
        end_date=end_dt
    )

    return {"books": books, "count": len(books)}


@router.get("/revenue/trends", summary="Get revenue trends")
async def get_revenue_trends(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_admin_user),
    revenue_service: RevenueService = Depends(get_revenue_service)
):
    """Get revenue trends over time (admin only)."""
    trends = await revenue_service.get_revenue_trends(
        days=days,
        granularity=granularity
    )

    return trends
```

---

### Phase 3: Admin Revenue Dashboard (High Priority)
**Goal**: Build admin UI to view revenue metrics
**Timeline**: 2-3 days
**Priority**: 🟡 High

#### 3.1 Revenue Dashboard Page
**File**: `frontend/src/pages/admin/RevenueDashboard.tsx` (NEW)

```tsx
/**
 * Revenue Dashboard - Admin Only
 * Shows total platform revenue, top earning books, trends
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DollarSign,
  TrendingUp,
  BookOpen,
  Users,
  BarChart2,
  Calendar
} from 'lucide-react';
import { api } from '../../lib/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function RevenueDashboard() {
  const [totalRevenue, setTotalRevenue] = useState(null);
  const [topBooks, setTopBooks] = useState([]);
  const [trends, setTrends] = useState([]);
  const [timeRange, setTimeRange] = useState('30'); // days
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRevenueData();
  }, [timeRange]);

  const loadRevenueData = async () => {
    setLoading(true);
    try {
      const [revenueRes, booksRes, trendsRes] = await Promise.all([
        api.admin.getTotalRevenue(),
        api.admin.getRevenueByBook({ limit: 10 }),
        api.admin.getRevenueTrends({ days: parseInt(timeRange) })
      ]);

      setTotalRevenue(revenueRes.data);
      setTopBooks(booksRes.data.books);
      setTrends(trendsRes.data.data);
    } catch (error) {
      console.error('Failed to load revenue data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
    </div>;
  }

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Revenue Dashboard</h1>
            <p className="text-gray-400">Platform revenue analytics and insights</p>
          </div>

          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>

        {/* Revenue Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="h-8 w-8 text-purple-400" />
              <span className="text-xs text-gray-400">TOTAL</span>
            </div>
            <p className="text-3xl font-bold text-white">
              ${totalRevenue?.total_revenue?.toFixed(2) || '0.00'}
            </p>
            <p className="text-sm text-gray-400 mt-1">Platform Revenue</p>
          </motion.div>

          {/* Listening Revenue */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-2">
              <BookOpen className="h-8 w-8 text-blue-400" />
              <span className="text-xs text-gray-400">LISTENING</span>
            </div>
            <p className="text-3xl font-bold text-white">
              ${totalRevenue?.breakdown?.listening?.revenue?.toFixed(2) || '0.00'}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              {totalRevenue?.breakdown?.listening?.percentage?.toFixed(1)}% of total
            </p>
          </motion.div>

          {/* AI Revenue */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="h-8 w-8 text-green-400" />
              <span className="text-xs text-gray-400">AI Q&A</span>
            </div>
            <p className="text-3xl font-bold text-white">
              ${totalRevenue?.breakdown?.ai_interactions?.revenue?.toFixed(2) || '0.00'}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              {totalRevenue?.breakdown?.ai_interactions?.percentage?.toFixed(1)}% of total
            </p>
          </motion.div>

          {/* Average Transaction */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-2">
              <Users className="h-8 w-8 text-yellow-400" />
              <span className="text-xs text-gray-400">AVG VALUE</span>
            </div>
            <p className="text-3xl font-bold text-white">
              ${totalRevenue?.average_transaction_value?.toFixed(2) || '0.00'}
            </p>
            <p className="text-sm text-gray-400 mt-1">Per Transaction</p>
          </motion.div>
        </div>

        {/* Revenue Trends Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gray-800 rounded-xl p-6"
        >
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
            <BarChart2 className="h-6 w-6 mr-2 text-purple-400" />
            Revenue Trends
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="total_revenue"
                stroke="#A855F7"
                strokeWidth={2}
                name="Total Revenue"
              />
              <Line
                type="monotone"
                dataKey="listening_revenue"
                stroke="#3B82F6"
                strokeWidth={2}
                name="Listening"
              />
              <Line
                type="monotone"
                dataKey="ai_revenue"
                stroke="#10B981"
                strokeWidth={2}
                name="AI Q&A"
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Top Earning Books */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gray-800 rounded-xl p-6"
        >
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
            <BookOpen className="h-6 w-6 mr-2 text-purple-400" />
            Top Earning Books
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="pb-3">Rank</th>
                  <th className="pb-3">Book</th>
                  <th className="pb-3">Author</th>
                  <th className="pb-3 text-right">Revenue</th>
                  <th className="pb-3 text-right">Listeners</th>
                  <th className="pb-3 text-right">Avg/User</th>
                </tr>
              </thead>
              <tbody>
                {topBooks.map((book, index) => (
                  <tr
                    key={book.book_id}
                    className="border-b border-gray-700/50 hover:bg-gray-700/30 transition"
                  >
                    <td className="py-3">
                      <span className="text-xl font-bold text-purple-400">#{index + 1}</span>
                    </td>
                    <td className="py-3">
                      <p className="text-white font-medium">{book.title}</p>
                    </td>
                    <td className="py-3 text-gray-400">{book.author}</td>
                    <td className="py-3 text-right">
                      <span className="text-white font-semibold">
                        ${book.total_revenue.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-3 text-right text-gray-400">
                      {book.unique_users}
                    </td>
                    <td className="py-3 text-right text-gray-400">
                      ${book.average_revenue_per_user.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
```

---

## Database Schema Changes

### No New Collections Needed!
All tracking uses existing `transactions` collection from shared wallet service.

### Required Metadata in Transactions:
```javascript
{
  "_id": ObjectId("..."),
  "wallet_id": "wallet_uuid",
  "type": "debit",
  "amount": -0.50,  // Negative for debit
  "status": "completed",
  "description": "Listening: The Great Gatsby - 5.0 minutes",
  "metadata": {
    "service": "inkwave_listening",  // or "inkwave_ai"
    "book_id": "book_123",
    "book_title": "The Great Gatsby",  // IMPORTANT for reporting
    "duration_minutes": 5.0,
    "rate_per_minute": 0.10
  },
  "created_at": ISODate("2025-11-12T10:30:00Z")
}
```

---

## Testing Strategy

### Unit Tests:
```bash
# Test wallet charging
pytest tests/test_wallet_charging.py -v

# Test revenue calculations
pytest tests/test_revenue_service.py -v

# Test analytics
pytest tests/test_analytics_service.py -v
```

### Integration Tests:
```bash
# Test full reading flow with charging
pytest tests/integration/test_reading_with_charging.py -v

# Test revenue reporting
pytest tests/integration/test_revenue_reporting.py -v
```

### Manual Testing Checklist:
- [ ] User with $10 can listen to ~100 minutes
- [ ] User with $0.05 cannot start listening (insufficient balance)
- [ ] Credits deducted every 10 seconds during listening
- [ ] Transaction recorded with correct book_id
- [ ] Analytics show correct per-book revenue
- [ ] Admin dashboard displays total revenue
- [ ] Top books ranked by revenue correctly

---

## Deployment Checklist

### Backend:
- [ ] Deploy updated `reading.py` with balance checks
- [ ] Deploy `revenue_service.py`
- [ ] Update admin routes with revenue endpoints
- [ ] Restart backend service
- [ ] Verify wallet service initialized
- [ ] Test charging endpoint

### Frontend:
- [ ] Build with updated AudioPlayer charging logic
- [ ] Deploy RevenueDashboard page
- [ ] Add admin navigation link
- [ ] Test in production
- [ ] Monitor error logs

### Database:
- [ ] Verify wallet transactions have metadata
- [ ] Check indexes on transactions collection
- [ ] Test analytics queries performance

---

## Monitoring & Alerts

### Metrics to Track:
1. **Failed Charges** - Users hitting insufficient balance
2. **Average Revenue Per User** - ARPU trending
3. **Revenue Growth** - Month-over-month, week-over-week
4. **Top Earning Books** - Which books drive revenue
5. **Charge Failures** - System errors during charging

### Alerts:
- 🚨 **Critical**: Charging system down (no charges in 10 minutes)
- ⚠️ **Warning**: High charge failure rate (>5%)
- ℹ️ **Info**: Daily revenue summary email

---

## Cost Optimization

### Current Pricing:
- Listening: $0.10/minute
- Voice Q&A: ~$0.04/question
- Welcome Bonus: $10.00

### Recommendations:
1. **Tiered Pricing**: Offer monthly subscriptions (unlimited listening for $9.99/month)
2. **Bulk Discounts**: Top-up bonuses (spend $50, get $5 free)
3. **Free Tier**: First 30 minutes free per month
4. **Book Pricing**: Some books cost more (premium content)

---

## Success Metrics

### KPIs to Measure:
1. **Monthly Recurring Revenue (MRR)**: Target $10k/month
2. **Average Revenue Per User (ARPU)**: Target $5/user/month
3. **Conversion Rate**: Trial to paid users >20%
4. **Churn Rate**: < 10% monthly
5. **Top-up Frequency**: Users add credits 2-3x/month

---

## Timeline Summary

| Phase | Task | Days | Priority |
|-------|------|------|----------|
| 1 | Pre-flight balance checks | 0.5 | 🔴 Critical |
| 1 | Automated charging in audio player | 1 | 🔴 Critical |
| 1 | Batch charging API | 0.5 | 🔴 Critical |
| 1 | Frontend charging integration | 1 | 🔴 Critical |
| 2 | Revenue service implementation | 1 | 🟡 High |
| 2 | Admin revenue API endpoints | 0.5 | 🟡 High |
| 2 | Per-book revenue tracking | 0.5 | 🟡 High |
| 3 | Admin revenue dashboard UI | 2 | 🟡 High |
| 3 | Revenue charts & visualizations | 1 | 🟡 High |
| | **Testing & Deployment** | 1 | 🔴 Critical |
| | **TOTAL** | **8-9 days** | |

---

## Risk Assessment

### High Risks:
1. **Users Run Out of Credits Mid-Session**
   - Mitigation: Low balance warnings, pause with friendly message

2. **Charging Failures**
   - Mitigation: Retry logic, error logging, manual reconciliation

3. **Revenue Calculation Errors**
   - Mitigation: Unit tests, cross-check with wallet transactions

4. **Performance Impact**
   - Mitigation: Batch charging (10-second intervals), indexed queries

---

## Next Steps

1. ✅ **You've reviewed the plan**
2. 🔲 **Approve the approach**
3. 🔲 **I implement Phase 1** (automated charging)
4. 🔲 **Test charging with real data**
5. 🔲 **I implement Phase 2** (revenue service)
6. 🔲 **I implement Phase 3** (admin dashboard)
7. 🔲 **Deploy to production**
8. 🔲 **Monitor & optimize**

---

**Ready to start implementation?** Which phase should we tackle first?

I recommend starting with **Phase 1 (Automated Charging)** since it's critical for monetization.
