"""
Shared State - Database for coordinating multiple agents
"""

import aiosqlite
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SharedState:
    """SQLite-based shared state for agent coordination"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
    
    async def initialize(self):
        """Initialize database schema"""
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db = await aiosqlite.connect(str(self.db_path))
        
        # Create tables
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS explored_pages (
                page_hash TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                state_json TEXT,
                first_visited TEXT,
                visit_count INTEGER DEFAULT 1
            )
        """)
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS explored_actions (
                action_hash TEXT PRIMARY KEY,
                action_json TEXT,
                executed_at TEXT,
                agent_id INTEGER
            )
        """)
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_type TEXT,
                severity TEXT,
                message TEXT,
                url TEXT,
                agent_id INTEGER,
                timestamp TEXT,
                details_json TEXT
            )
        """)
        
        await self.db.commit()
        logger.info("Shared state database initialized")
    
    async def is_page_explored(self, page_hash: str) -> bool:
        """Check if page has been explored"""
        
        async with self.db.execute(
            "SELECT 1 FROM explored_pages WHERE page_hash = ?",
            (page_hash,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    
    async def mark_page_explored(self, page_hash: str, state: Dict):
        """Mark page as explored"""
        
        try:
            await self.db.execute("""
                INSERT INTO explored_pages (page_hash, url, title, state_json, first_visited)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(page_hash) DO UPDATE SET visit_count = visit_count + 1
            """, (
                page_hash,
                state.get('url', ''),
                state.get('title', ''),
                json.dumps(state),
                datetime.now().isoformat()
            ))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to mark page explored: {e}")
    
    async def is_action_explored(self, action_hash: str) -> bool:
        """Check if action has been executed"""
        
        async with self.db.execute(
            "SELECT 1 FROM explored_actions WHERE action_hash = ?",
            (action_hash,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    
    async def mark_action_explored(self, action_hash: str, action: Dict):
        """Mark action as executed"""
        
        try:
            await self.db.execute("""
                INSERT OR IGNORE INTO explored_actions (action_hash, action_json, executed_at, agent_id)
                VALUES (?, ?, ?, ?)
            """, (
                action_hash,
                json.dumps(action),
                datetime.now().isoformat(),
                action.get('agent_id', -1)
            ))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to mark action explored: {e}")
    
    async def get_explored_pages(self, limit: int = 100) -> List[Dict]:
        """Get list of explored pages"""
        
        async with self.db.execute("""
            SELECT url, title, first_visited
            FROM explored_pages
            ORDER BY first_visited DESC
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            
            return [
                {
                    'url': row[0],
                    'title': row[1],
                    'visited': row[2]
                }
                for row in rows
            ]
    
    async def add_finding(self, finding: Dict):
        """Add a bug or issue finding"""
        
        try:
            await self.db.execute("""
                INSERT INTO findings (
                    finding_type, severity, message, url, agent_id, timestamp, details_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                finding.get('type', 'unknown'),
                finding.get('severity', 'unknown'),
                finding.get('message', ''),
                finding.get('url', ''),
                finding.get('agent_id', -1),
                finding.get('timestamp', datetime.now().isoformat()),
                json.dumps(finding)
            ))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to add finding: {e}")
    
    async def get_all_findings(self) -> List[Dict]:
        """Get all bug findings"""
        
        async with self.db.execute("""
            SELECT finding_type, severity, message, url, agent_id, timestamp, details_json
            FROM findings
            ORDER BY timestamp DESC
        """) as cursor:
            rows = await cursor.fetchall()
            
            findings = []
            for row in rows:
                try:
                    details = json.loads(row[6])
                    findings.append(details)
                except:
                    findings.append({
                        'type': row[0],
                        'severity': row[1],
                        'message': row[2],
                        'url': row[3],
                        'agent_id': row[4],
                        'timestamp': row[5]
                    })
            
            return findings
    
    async def get_coverage_stats(self) -> Dict:
        """Get coverage statistics"""
        
        stats = {
            'pages_explored': 0,
            'actions_executed': 0,
            'findings_count': 0,
            'unique_urls': 0
        }
        
        try:
            # Pages explored
            async with self.db.execute("SELECT COUNT(*) FROM explored_pages") as cursor:
                row = await cursor.fetchone()
                stats['pages_explored'] = row[0] if row else 0
            
            # Actions executed
            async with self.db.execute("SELECT COUNT(*) FROM explored_actions") as cursor:
                row = await cursor.fetchone()
                stats['actions_executed'] = row[0] if row else 0
            
            # Findings
            async with self.db.execute("SELECT COUNT(*) FROM findings") as cursor:
                row = await cursor.fetchone()
                stats['findings_count'] = row[0] if row else 0
            
            # Unique URLs
            async with self.db.execute("SELECT COUNT(DISTINCT url) FROM explored_pages") as cursor:
                row = await cursor.fetchone()
                stats['unique_urls'] = row[0] if row else 0
                
        except Exception as e:
            logger.error(f"Failed to get coverage stats: {e}")
        
        return stats
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            logger.info("Shared state database closed")
