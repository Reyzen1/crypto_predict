# temp/generate_models.py
"""
CryptoPredict Model Files Generator
Generates all ORM model files from the complete artifact
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class ModelFilesGenerator:
    """
    Generate all ORM model files from the complete artifact
    """
    
    def __init__(self, artifact_file: str, output_dir: str = "backend/app/models"):
        self.artifact_file = artifact_file
        self.output_dir = output_dir
        self.files_created = []
        
    def read_artifact(self) -> str:
        """Read the artifact content from file"""
        try:
            with open(self.artifact_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Error: Artifact file '{self.artifact_file}' not found!")
            print("💡 Please save the artifact content to a file and try again.")
            return ""
        except Exception as e:
            print(f"❌ Error reading artifact file: {e}")
            return ""
    
    def parse_files(self, content: str) -> Dict[str, str]:
        """
        Parse the artifact content and extract individual files
        Returns dict with file_path -> file_content
        """
        files = {}
        
        # Regex pattern to match file headers like:
        # # ==================================================
        # # backend/app/models/__init__.py
        # # ==================================================
        file_pattern = re.compile(
            r'# =+\s*\n# (backend/app/models/[^\n]+)\s*\n# =+\s*\n(.*?)(?=# =+|$)', 
            re.DOTALL
        )
        
        matches = file_pattern.findall(content)
        
        for file_path, file_content in matches:
            # Clean up the file content
            file_content = file_content.strip()
            
            # Remove the docstring comment if it's at the beginning
            lines = file_content.split('\n')
            if lines and lines[0].startswith('"""'):
                # Find the end of the docstring
                end_idx = 1
                while end_idx < len(lines) and not lines[end_idx].strip().endswith('"""'):
                    end_idx += 1
                if end_idx < len(lines):
                    end_idx += 1
                    file_content = '\n'.join(lines[end_idx:]).strip()
            
            files[file_path] = file_content
            
        return files
    
    def create_directory_structure(self):
        """Create the necessary directory structure"""
        directories = [
            self.output_dir,
            f"{self.output_dir}/core",
            f"{self.output_dir}/market", 
            f"{self.output_dir}/sectors",
            f"{self.output_dir}/trading",
            f"{self.output_dir}/watchlist",
            f"{self.output_dir}/system"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")
    
    def clean_file_content(self, content: str, file_path: str) -> str:
        """
        Clean and format file content for writing
        """
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty comment lines or artifact markers
            if line.strip() == '#' or line.startswith('# ==='):
                continue
            
            # Skip the file path comment at the beginning
            if file_path in line and line.startswith('# '):
                continue
                
            cleaned_lines.append(line)
        
        # Join and clean up multiple empty lines
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive empty lines
        cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)
        
        # Ensure file ends with single newline
        cleaned_content = cleaned_content.strip() + '\n'
        
        return cleaned_content
    
    def write_file(self, file_path: str, content: str):
        """Write content to a file"""
        try:
            # Convert artifact path to actual file path
            relative_path = file_path.replace('backend/app/models/', '')
            full_path = os.path.join(self.output_dir, relative_path)
            
            # Clean the content
            cleaned_content = self.clean_file_content(content, file_path)
            
            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            self.files_created.append(full_path)
            print(f"✅ Created: {full_path}")
            
        except Exception as e:
            print(f"❌ Error writing file {file_path}: {e}")
    
    def validate_files(self):
        """Validate that all expected files were created"""
        expected_files = [
            '__init__.py',
            'database_setup.py',
            'core/__init__.py',
            'core/user.py',
            'core/crypto.py',
            'core/price.py', 
            'core/prediction.py',
            'market/__init__.py',
            'market/regime.py',
            'market/sentiment.py',
            'market/dominance.py',
            'market/indicators.py',
            'sectors/__init__.py',
            'sectors/sector.py',
            'sectors/performance.py',
            'sectors/rotation.py',
            'trading/__init__.py',
            'trading/signal.py',
            'trading/execution.py',
            'trading/risk.py',
            'watchlist/__init__.py',
            'watchlist/watchlist.py',
            'watchlist/suggestion.py',
            'watchlist/review.py',
            'system/__init__.py',
            'system/ai_model.py',
            'system/health.py',
            'system/info.py',
            'system/notification.py',
        ]
        
        missing_files = []
        for expected_file in expected_files:
            full_path = os.path.join(self.output_dir, expected_file)
            if not os.path.exists(full_path):
                missing_files.append(expected_file)
        
        if missing_files:
            print(f"\n⚠️  Warning: {len(missing_files)} expected files were not created:")
            for file in missing_files:
                print(f"   - {file}")
        else:
            print(f"\n✅ All {len(expected_files)} expected files created successfully!")
    
    def add_missing_imports(self):
        """Add any missing imports that might be needed"""
        import_fixes = {
            'core/user.py': [
                'from sqlalchemy import DECIMAL',
                'from app.core.database import Base'
            ],
            'core/crypto.py': [
                'from sqlalchemy import Text',
                'from app.core.database import Base'
            ],
            'core/price.py': [
                'from app.core.database import Base'
            ],
            'trading/signal.py': [
                'from app.core.database import Base'
            ]
        }
        
        for file_path, imports in import_fixes.items():
            full_path = os.path.join(self.output_dir, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if imports are missing and add them
                    for import_line in imports:
                        if import_line not in content:
                            # Add import after existing imports
                            lines = content.split('\n')
                            insert_idx = 0
                            for i, line in enumerate(lines):
                                if line.startswith('from ') or line.startswith('import '):
                                    insert_idx = i + 1
                            
                            lines.insert(insert_idx, import_line)
                            content = '\n'.join(lines)
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                except Exception as e:
                    print(f"⚠️  Warning: Could not fix imports for {file_path}: {e}")
    
    def preview_files(self, files: Dict[str, str]):
        """Preview files that will be generated"""
        print(f"📋 Preview: {len(files)} files will be generated:")
        print("-" * 40)
        
        domain_counts = {}
        for file_path in files.keys():
            if '/core/' in file_path:
                domain_counts['core'] = domain_counts.get('core', 0) + 1
            elif '/market/' in file_path:
                domain_counts['market'] = domain_counts.get('market', 0) + 1  
            elif '/sectors/' in file_path:
                domain_counts['sectors'] = domain_counts.get('sectors', 0) + 1
            elif '/trading/' in file_path:
                domain_counts['trading'] = domain_counts.get('trading', 0) + 1
            elif '/watchlist/' in file_path:
                domain_counts['watchlist'] = domain_counts.get('watchlist', 0) + 1
            elif '/system/' in file_path:
                domain_counts['system'] = domain_counts.get('system', 0) + 1
            else:
                domain_counts['root'] = domain_counts.get('root', 0) + 1
        
        for domain, count in domain_counts.items():
            print(f"  📁 {domain}: {count} files")
        
        print("\n📝 Files to be created:")
        for file_path in sorted(files.keys()):
            relative_path = file_path.replace('backend/app/models/', '')
            file_size = len(files[file_path])
            print(f"   ✅ {relative_path} ({file_size:,} chars)")
    
    def generate(self, preview_only: bool = False):
        """Main generation process"""
        print("🚀 Starting CryptoPredict Model Files Generation...")
        print("=" * 60)
        
        # Step 1: Read artifact
        print("📖 Reading artifact content...")
        content = self.read_artifact()
        if not content:
            return False
        
        print(f"✅ Artifact content loaded ({len(content):,} characters)")
        
        # Step 2: Parse files from artifact
        print("\n🔍 Parsing files from artifact...")
        files = self.parse_files(content)
        print(f"✅ Found {len(files)} files to generate")
        
        if not files:
            print("❌ No files found in artifact. Please check the artifact format.")
            print("💡 Make sure artifact contains file path comments like:")
            print("   # ==================================================")
            print("   # backend/app/models/__init__.py")
            print("   # ==================================================")
            return False
        
        # Step 2.5: Preview mode
        if preview_only:
            self.preview_files(files)
            print(f"\n📁 Output directory would be: {self.output_dir}")
            print("💡 Run without --preview to actually generate the files.")
            return True
        
        # Step 3: Create directory structure
        print("\n📁 Creating directory structure...")
        self.create_directory_structure()
        
        # Step 4: Generate files
        print(f"\n📝 Generating {len(files)} model files...")
        for file_path, file_content in files.items():
            self.write_file(file_path, file_content)
        
        # Step 5: Fix any missing imports
        print("\n🔧 Fixing imports...")
        self.add_missing_imports()
        
        # Step 6: Validate results
        print("\n✅ Validation...")
        self.validate_files()
        
        # Step 7: Summary
        print("\n" + "=" * 60)
        print("🎉 Model Generation Complete!")
        print(f"📊 Generated {len(self.files_created)} files")
        print(f"📁 Output directory: {self.output_dir}")
        
        if len(self.files_created) <= 10:
            print("\n📋 Generated files:")
            for file_path in sorted(self.files_created):
                print(f"   ✅ {file_path}")
        else:
            print(f"\n📋 Generated {len(self.files_created)} files in domain structure")
        
        print("\n🚀 Ready for Phase 2 development!")
        return True
    
    def show_usage(self):
        """Show usage instructions"""
        print("💡 Usage Instructions:")
        print("1. Save the artifact content to a file (e.g., 'models_artifact.py')")
        print("2. Run this script:")
        print("   python generate_models.py")
        print("   or")
        print("   python generate_models.py --input models_artifact.py --output custom/path")
        print("\n📂 Default paths:")
        print(f"   Input: {self.artifact_file}")
        print(f"   Output: {self.output_dir}")


def main():
    """Main function with command line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate CryptoPredict ORM model files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_models.py                                    # Basic usage
  python generate_models.py --preview                          # Preview only
  python generate_models.py -i models.py -o custom/path        # Custom paths
  python generate_models.py --usage                            # Show instructions
        """
    )
    
    parser.add_argument('--input', '-i', 
                       default='models_artifact.py',
                       help='Input artifact file path (default: models_artifact.py)')
    parser.add_argument('--output', '-o',
                       default='backend/app/models', 
                       help='Output directory path (default: backend/app/models)')
    parser.add_argument('--preview', '-p', action='store_true',
                       help='Preview files that will be generated without creating them')
    parser.add_argument('--usage', action='store_true',
                       help='Show detailed usage instructions')
    
    args = parser.parse_args()
    
    generator = ModelFilesGenerator(args.input, args.output)
    
    if args.usage:
        generator.show_usage()
        return
    
    # Check if artifact file exists
    if not os.path.exists(args.input):
        print(f"❌ Artifact file '{args.input}' not found!")
        print("\n💡 Steps to use this script:")
        print("1. Save the complete artifact content to a file (e.g., 'models_artifact.py')")
        print("2. Run: python generate_models.py --input models_artifact.py")
        print("\nAlternatively:")
        print("- Preview mode: python generate_models.py --preview")
        print("- Help: python generate_models.py --usage")
        return
    
    # Generate files
    success = generator.generate(preview_only=args.preview)
    
    if success and not args.preview:
        print("\n🎯 Next steps:")
        print("1. Review the generated files")
        print("2. Test imports: python -c 'from backend.app.models import *'")
        print("3. Run database setup: python -c 'from backend.app.models.database_setup import validate_models; validate_models()'")
        print("4. Start Phase 2 development! 🚀")
    elif success and args.preview:
        print("\n🎯 To generate files:")
        print(f"python {os.path.basename(__file__)} --input {args.input} --output {args.output}")
    else:
        print("\n❌ Generation failed. Please check the error messages above.")


if __name__ == "__main__":
    main()