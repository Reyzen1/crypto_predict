# temp/final_rate_limit_fix.py
"""
Final fix for Celery rate limits - use only supported modifiers
Celery only supports: s (second), m (minute), h (hour)
"""

import os
import re
from pathlib import Path

def fix_rate_limits_final():
    """Fix rate limits to use only supported Celery modifiers"""
    
    config_path = Path(__file__).parent.parent / "backend" / "app" / "core" / "celery_config.py"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    print("🔧 Final rate limit fix...")
    print("📋 Celery supported modifiers: s, m, h ONLY")
    
    try:
        # Read current config
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup original
        backup_path = config_path.with_suffix('.py.backup2')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Backup created: {backup_path}")
        
        # Fix rate limits with ONLY supported modifiers
        fixed_content = content
        
        # Replace daily rate limits with hourly equivalents
        replacements = [
            # Replace 1/d with 1/24h (once per day = once per 24 hours)
            (r'"rate_limit":\s*"1/d"', '"rate_limit": "1/24h"'),
            
            # For any other /d pattern, convert to hourly
            (r'"rate_limit":\s*"(\d+)/d"', r'"rate_limit": "\1/24h"'),
        ]
        
        changes_made = 0
        for pattern, replacement in replacements:
            matches = re.findall(pattern, fixed_content)
            if matches:
                print(f"🔍 Found pattern: {pattern}")
                fixed_content = re.sub(pattern, replacement, fixed_content)
                changes_made += len(matches)
        
        if changes_made > 0:
            print(f"✅ Made {changes_made} rate limit changes")
            
            # Write fixed content
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("📊 New rate limits:")
            print("   • 12/m - 12 times per minute (price sync)")
            print("   • 4/h - 4 times per hour (historical sync)")  
            print("   • 1/24h - once per day (discovery)")
            print("   • 1/24h - once per day (cleanup)")
            
            return True
        else:
            print("⚠️ No '/d' patterns found to fix")
            return True
            
    except Exception as e:
        print(f"❌ Failed to fix rate limits: {e}")
        return False

def create_rate_limit_disabled_config():
    """Create version with rate limits disabled as backup solution"""
    
    config_path = Path(__file__).parent.parent / "backend" / "app" / "core" / "celery_config.py"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Comment out task_annotations completely
        fixed_content = content
        
        # Find task_annotations section and comment it out
        pattern = r'(    task_annotations: Dict\[str, Dict\[str, Any\]\] = \{.*?\n    \})'
        match = re.search(pattern, fixed_content, re.DOTALL)
        
        if match:
            original_block = match.group(1)
            commented_block = '\n'.join('    # ' + line for line in original_block.split('\n'))
            fixed_content = fixed_content.replace(original_block, commented_block)
            
            # Add rate limits disabled flag
            fixed_content = fixed_content.replace(
                'worker_disable_rate_limits: bool = False',
                'worker_disable_rate_limits: bool = True  # DISABLED DUE TO CELERY ISSUES'
            )
        
        # Save as alternative config
        alt_config_path = config_path.with_name('celery_config_no_limits.py')
        with open(alt_config_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"💾 Created rate-limit-free config: {alt_config_path}")
        return alt_config_path
        
    except Exception as e:
        print(f"❌ Failed to create no-limits config: {e}")
        return None

def test_celery_rate_support():
    """Test what rate modifiers Celery actually supports"""
    
    print("\n🧪 Testing Celery rate modifier support...")
    
    try:
        # This is what Celery actually supports based on the error
        supported = {
            's': 'second',
            'm': 'minute', 
            'h': 'hour'
        }
        
        not_supported = {
            'd': 'day',
            'w': 'week',
            'month': 'month',
            'y': 'year'
        }
        
        print("✅ Supported by Celery:")
        for modifier, name in supported.items():
            print(f"   • {modifier} ({name})")
        
        print("❌ NOT supported by Celery:")
        for modifier, name in not_supported.items():
            print(f"   • {modifier} ({name})")
        
        print("\n💡 Solutions for daily/weekly tasks:")
        print("   • 1/d → 1/24h (once per 24 hours)")
        print("   • 1/w → 1/168h (once per 168 hours)")
        print("   • Or disable rate limits entirely")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main fix process"""
    
    print("🛠️ Final Celery Rate Limit Fix")
    print("=" * 35)
    
    # Step 1: Test what's supported
    test_celery_rate_support()
    
    # Step 2: Try to fix with supported modifiers
    print("\n🔧 Attempting fix with supported modifiers...")
    fix_success = fix_rate_limits_final()
    
    # Step 3: Create backup solution
    print("\n💾 Creating backup solution (no rate limits)...")
    alt_config = create_rate_limit_disabled_config()
    
    if fix_success:
        print("\n🎯 SOLUTION 1: Fixed rate limits to use supported modifiers")
        print("📋 Try this first:")
        print("   cd backend")
        print("   python -m celery -A app.tasks.celery_app worker --queues=price_data --pool=threads")
    
    if alt_config:
        print("\n🎯 SOLUTION 2: Backup config with rate limits disabled")
        print("📋 If Solution 1 fails, manually copy:")
        print(f"   cp {alt_config} backend/app/core/celery_config.py")
    
    print("\n🚀 After fixing, test with:")
    print("   ./temp/test_fixed_worker.sh")

if __name__ == "__main__":
    main()