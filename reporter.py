"""
HTML Reporter - Generates comprehensive test reports
"""

import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import json

from config import Config

logger = logging.getLogger(__name__)


class HTMLReporter:
    """Generates HTML reports from test findings"""
    
    def __init__(self, findings: List[Dict], coverage: Dict, duration: float, config: Config):
        self.findings = findings
        self.coverage = coverage
        self.duration = duration
        self.config = config
    
    def generate(self) -> Path:
        """Generate HTML report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.config.output_dir / f"test_report_{timestamp}.html"
        
        html = self._build_html()
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Report saved to {report_path}")
        return report_path
    
    def _build_html(self) -> str:
        """Build HTML report content"""
        
        # Group findings by severity
        critical = [f for f in self.findings if f.get('severity') == 'critical']
        high = [f for f in self.findings if f.get('severity') == 'high']
        medium = [f for f in self.findings if f.get('severity') == 'medium']
        low = [f for f in self.findings if f.get('severity') == 'low']
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Testing Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 18px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .stat-card .label {{
            color: #6c757d;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #212529;
        }}
        
        .findings {{
            padding: 40px;
        }}
        
        .findings h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #212529;
        }}
        
        .severity-section {{
            margin-bottom: 40px;
        }}
        
        .severity-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 6px;
        }}
        
        .severity-critical {{
            background: #fee;
            color: #c00;
        }}
        
        .severity-high {{
            background: #fef0e5;
            color: #e67e22;
        }}
        
        .severity-medium {{
            background: #fff9e6;
            color: #f39c12;
        }}
        
        .severity-low {{
            background: #e8f5e9;
            color: #27ae60;
        }}
        
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-right: 10px;
        }}
        
        .finding-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        
        .finding-type {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .finding-message {{
            color: #495057;
            margin-bottom: 12px;
        }}
        
        .finding-meta {{
            display: flex;
            gap: 20px;
            font-size: 12px;
            color: #6c757d;
        }}
        
        .finding-url {{
            color: #007bff;
            word-break: break-all;
        }}
        
        .no-findings {{
            padding: 40px;
            text-align: center;
            color: #6c757d;
        }}
        
        .footer {{
            padding: 20px 40px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐝 Autonomous Testing Report</h1>
            <div class="subtitle">Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</div>
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="label">Duration</div>
                <div class="value">{int(self.duration / 60)}m</div>
            </div>
            <div class="stat-card">
                <div class="label">Pages Explored</div>
                <div class="value">{self.coverage.get('pages_explored', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Actions Executed</div>
                <div class="value">{self.coverage.get('actions_executed', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Findings</div>
                <div class="value">{len(self.findings)}</div>
            </div>
        </div>
        
        <div class="findings">
            <h2>Findings by Severity</h2>
            
            {self._render_severity_section('Critical', critical, 'critical')}
            {self._render_severity_section('High', high, 'high')}
            {self._render_severity_section('Medium', medium, 'medium')}
            {self._render_severity_section('Low', low, 'low')}
        </div>
        
        <div class="footer">
            <strong>Target URL:</strong> {self.config.base_url}<br>
            <strong>Test Configuration:</strong> {self.config.model_name} via Ollama
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _render_severity_section(self, title: str, findings: List[Dict], severity: str) -> str:
        """Render findings section for a severity level"""
        
        if not findings:
            return ""
        
        html = f"""
            <div class="severity-section">
                <div class="severity-header severity-{severity}">
                    <span class="severity-badge">{severity.upper()}</span>
                    <span>{title} ({len(findings)} found)</span>
                </div>
        """
        
        for finding in findings:
            html += f"""
                <div class="finding-card">
                    <div class="finding-type">{finding.get('type', 'Unknown').replace('_', ' ').title()}</div>
                    <div class="finding-message">{finding.get('message', 'No description')}</div>
                    <div class="finding-meta">
                        <div><strong>URL:</strong> <span class="finding-url">{finding.get('url', 'N/A')}</span></div>
                        <div><strong>Agent:</strong> {finding.get('agent_id', 'N/A')}</div>
                        <div><strong>Time:</strong> {finding.get('timestamp', 'N/A')[:19]}</div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        """
        
        return html
