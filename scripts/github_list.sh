#!/bin/bash

# File: temp/gitbash_list.sh
# GitHub Repository Files Lister
# Script to list all files from a specific GitHub repository using git and GitHub API

set -e


echo "🐍 Starting GitHub Repository Files Lister"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi


# Default values
REPO_URL="https://github.com/Reyzen1/crypto_predict"
OUTPUT_DIR="./temp/repo_files_output"
TEMP_DIR="/tmp/repo_clone_$$"
GITHUB_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show help
show_help() {
    cat << EOF
GitHub Repository Files Lister

Usage: $0 [OPTIONS] [REPOSITORY_URL]

OPTIONS:
    -h, --help          Show this help message
    -t, --token TOKEN   GitHub personal access token (for private repos)
    -o, --output DIR    Output directory (default: ./temp/repo_files_output)
    --csv               Export to CSV format
    --json              Export to JSON format
    --txt               Export to TXT format (default)
    --all               Export to all formats

EXAMPLES:
    $0
    $0 https://github.com/user/repo
    $0 -t your_token https://github.com/user/private-repo
    $0 --csv --json https://github.com/user/repo

EOF
}

# Function to parse repository URL
parse_repo_url() {
    local url="$1"
    
    # Remove .git suffix if present
    url="${url%.git}"
    
    # Extract owner and repo name
    if [[ "$url" =~ https://github.com/([^/]+)/([^/]+) ]]; then
        REPO_OWNER="${BASH_REMATCH[1]}"
        REPO_NAME="${BASH_REMATCH[2]}"
        return 0
    elif [[ "$url" =~ ^([^/]+)/([^/]+)$ ]]; then
        REPO_OWNER="${BASH_REMATCH[1]}"
        REPO_NAME="${BASH_REMATCH[2]}"
        return 0
    else
        return 1
    fi
}

# Function to get repository info from GitHub API
get_repo_info() {
    local api_url="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME"
    local headers=""
    
    if [[ -n "$GITHUB_TOKEN" ]]; then
        headers="-H \"Authorization: token $GITHUB_TOKEN\""
    fi
    
    eval "curl -s $headers \"$api_url\"" 2>/dev/null || echo "{}"
}

# Function to clone repository
clone_repository() {
    print_info "Cloning repository to temporary directory..."
    
    # Clean up temp directory if exists
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Clone the repository
    if [[ -n "$GITHUB_TOKEN" ]]; then
        # Use token for private repos
        local auth_url="${REPO_URL/https:\/\/github.com/https://$GITHUB_TOKEN@github.com}"
        git clone --depth 1 "$auth_url" "$TEMP_DIR" 2>/dev/null
    else
        git clone --depth 1 "$REPO_URL" "$TEMP_DIR" 2>/dev/null
    fi
    
    if [[ $? -ne 0 ]]; then
        print_error "Failed to clone repository. Check URL and permissions."
        return 1
    fi
    
    print_success "Repository cloned successfully"
}

# Function to scan files
scan_files() {
    print_info "Scanning repository files..."
    
    cd "$TEMP_DIR"
    
    # Ensure output directory exists
    mkdir -p "$OUTPUT_DIR"
    
    print_info "Scanning all files including hidden files..."
    
    # Get all files (excluding .git directory) - comprehensive search
    # First pass: regular files
    find . -type f ! -path "./.git/*" ! -path "./.git" ! -name ".git*" -print > "$OUTPUT_DIR/files_list_temp1.txt"
    
    # Second pass: include hidden files (starting with .)
    find . -name ".*" -type f ! -path "./.git/*" ! -name ".git*" -print >> "$OUTPUT_DIR/files_list_temp1.txt"
    
    # Third pass: be extra thorough with different find syntax
    find . -type f \( ! -path "./.git/*" ! -name ".git*" \) -print >> "$OUTPUT_DIR/files_list_temp1.txt"
    
    # Remove duplicates and sort
    sort "$OUTPUT_DIR/files_list_temp1.txt" | uniq > "$OUTPUT_DIR/files_list_raw.txt"
    rm -f "$OUTPUT_DIR/files_list_temp1.txt"
    
    # Count files and directories
    local total_files=$(wc -l < "$OUTPUT_DIR/files_list_raw.txt")
    local total_dirs=$(find . -type d ! -path "./.git/*" ! -name ".git" | wc -l)
    
    print_success "Found $total_files files in $total_dirs directories"
    
    # Show some examples of found files
    print_info "Sample of found files:"
    head -10 "$OUTPUT_DIR/files_list_raw.txt" | while read -r file; do
        echo "  📄 $file"
    done
    
    if [[ $total_files -gt 10 ]]; then
        echo "  ... and $((total_files - 10)) more files"
    fi
    
    cd - > /dev/null
}

# Function to export to TXT format
export_to_txt() {
    local output_file="$OUTPUT_DIR/${REPO_OWNER}_${REPO_NAME}_files_$(date +%Y%m%d_%H%M%S).txt"
    
    print_info "Exporting to TXT format..."
    
    {
        echo "Repository Files List"
        echo "====================="
        echo "Repository: $REPO_OWNER/$REPO_NAME"
        echo "URL: $REPO_URL"
        echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        
        cd "$TEMP_DIR"
        
        # Group files by directory
        local current_dir=""
        while IFS= read -r file; do
            # Remove leading ./
            file="${file#./}"
            
            local dir_path=$(dirname "$file")
            [[ "$dir_path" == "." ]] && dir_path="/"
            
            if [[ "$dir_path" != "$current_dir" ]]; then
                echo ""
                echo "📁 Directory: $dir_path"
                echo "$(printf '─%.0s' {1..50})"
                current_dir="$dir_path"
            fi
            
            local filename=$(basename "$file")
            local size=""
            if [[ -f "$file" ]]; then
                local bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
                if [[ $bytes -gt 1048576 ]]; then
                    size=$(echo "scale=2; $bytes/1048576" | bc -l 2>/dev/null || echo "0")
                    size="${size} MB"
                elif [[ $bytes -gt 1024 ]]; then
                    size=$(echo "scale=2; $bytes/1024" | bc -l 2>/dev/null || echo "0")
                    size="${size} KB"
                else
                    size="${bytes} B"
                fi
            fi
            
            echo "  📄 $filename"
            
        done < <(find . -type f ! -path "./.git/*" ! -name ".git*" | sort)
        
        cd - > /dev/null
        
    } > "$output_file"
    
    print_success "TXT file exported: $output_file"
}

# Function to export to CSV format
export_to_csv() {
    local output_file="$OUTPUT_DIR/${REPO_OWNER}_${REPO_NAME}_files_$(date +%Y%m%d_%H%M%S).csv"
    
    print_info "Exporting to CSV format..."
    
    {
        echo "repository,path,filename,size_bytes,size_human,extension,directory"
        
        cd "$TEMP_DIR"
        
        while IFS= read -r file; do
            # Remove leading ./
            file="${file#./}"
            
            local filename=$(basename "$file")
            local dir_path=$(dirname "$file")
            [[ "$dir_path" == "." ]] && dir_path="/"
            
            local extension="${filename##*.}"
            [[ "$extension" == "$filename" ]] && extension=""
            
            local size_bytes="0"
            local size_human="0 B"
            
            if [[ -f "$file" ]]; then
                size_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
                
                if [[ $size_bytes -gt 1048576 ]]; then
                    local size_mb=$(echo "scale=2; $size_bytes/1048576" | bc -l 2>/dev/null || echo "0")
                    size_human="${size_mb} MB"
                elif [[ $size_bytes -gt 1024 ]]; then
                    local size_kb=$(echo "scale=2; $size_bytes/1024" | bc -l 2>/dev/null || echo "0")
                    size_human="${size_kb} KB"
                else
                    size_human="${size_bytes} B"
                fi
            fi
            
            echo "\"$REPO_OWNER/$REPO_NAME\",\"$file\",\"$filename\",$size_bytes,\"$size_human\",\"$extension\",\"$dir_path\""
            
        done < <(find . -type f ! -path "./.git/*" ! -name ".git*" | sort)
        
        cd - > /dev/null
        
    } > "$output_file"
    
    print_success "CSV file exported: $output_file"
}

# Function to export to JSON format
export_to_json() {
    local output_file="$OUTPUT_DIR/${REPO_OWNER}_${REPO_NAME}_files_$(date +%Y%m%d_%H%M%S).json"
    
    print_info "Exporting to JSON format..."
    
    {
        echo "{"
        echo "  \"repository\": {"
        echo "    \"owner\": \"$REPO_OWNER\","
        echo "    \"name\": \"$REPO_NAME\","
        echo "    \"url\": \"$REPO_URL\","
        echo "    \"scanned_at\": \"$(date -Iseconds)\""
        echo "  },"
        echo "  \"files\": ["
        
        cd "$TEMP_DIR"
        
        local first=true
        while IFS= read -r file; do
            # Remove leading ./
            file="${file#./}"
            
            [[ "$first" == true ]] && first=false || echo ","
            
            local filename=$(basename "$file")
            local dir_path=$(dirname "$file")
            [[ "$dir_path" == "." ]] && dir_path="/"
            
            local extension="${filename##*.}"
            [[ "$extension" == "$filename" ]] && extension=""
            
            local size_bytes="0"
            if [[ -f "$file" ]]; then
                size_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            fi
            
            echo -n "    {"
            echo -n "\"path\":\"$file\","
            echo -n "\"filename\":\"$filename\","
            echo -n "\"directory\":\"$dir_path\","
            echo -n "\"extension\":\"$extension\","
            echo -n "\"size_bytes\":$size_bytes"
            echo -n "}"
            
        done < <(find . -type f ! -path "./.git/*" ! -name ".git*" | sort)
        
        echo ""
        echo "  ]"
        echo "}"
        
        cd - > /dev/null
        
    } > "$output_file"
    
    print_success "JSON file exported: $output_file"
}

# Function to show directory tree
show_directory_tree() {
    print_info "Directory structure:"
    
    cd "$TEMP_DIR"
    
    # Use tree command if available, otherwise use find
    if command -v tree &> /dev/null; then
        tree -a -I '.git'
    else
        # Custom tree-like output using find
        find . -not -path './.git/*' -not -name '.git' | sed -e "s/[^-][^\/]*\// |/g" -e "s/|\([^ ]\)/|-\1/"
    fi
    
    cd - > /dev/null
    echo ""
}
generate_summary() {
    print_info "Generating summary..."
    
    cd "$TEMP_DIR"
    
    local total_files=$(find . -type f ! -path "./.git/*" ! -name ".git*" | wc -l)
    local total_dirs=$(find . -type d ! -path "./.git/*" ! -name ".git" | wc -l)
    
    # Calculate total size
    local total_size=0
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            total_size=$((total_size + size))
        fi
    done < <(find . -type f ! -path "./.git/*" ! -name ".git*")
    
    # Count file extensions
    echo "" > "$OUTPUT_DIR/extensions_temp.txt"
    find . -type f ! -path "./.git/*" ! -name ".git*" | while read -r file; do
        local ext="${file##*.}"
        [[ "$ext" == "$file" ]] && ext="no_extension"
        echo "$ext" >> "$OUTPUT_DIR/extensions_temp.txt"
    done
    
    cd - > /dev/null
    
    echo ""
    echo "📊 Repository Summary"
    echo "===================="
    echo "Repository: $REPO_OWNER/$REPO_NAME"
    echo "Total files: $total_files"
    echo "Total directories: $total_dirs"
    
    if [[ $total_size -gt 1048576 ]]; then
        local size_mb=$(echo "scale=2; $total_size/1048576" | bc -l 2>/dev/null || echo "0")
        echo "Total size: ${size_mb} MB"
    elif [[ $total_size -gt 1024 ]]; then
        local size_kb=$(echo "scale=2; $total_size/1024" | bc -l 2>/dev/null || echo "0")
        echo "Total size: ${size_kb} KB"
    else
        echo "Total size: ${total_size} bytes"
    fi
    
    echo ""
    echo "📁 File types:"
    if [[ -f "$OUTPUT_DIR/extensions_temp.txt" ]]; then
        sort "$OUTPUT_DIR/extensions_temp.txt" | uniq -c | sort -nr | head -10 | while read -r count ext; do
            echo "  $ext: $count files"
        done
        rm -f "$OUTPUT_DIR/extensions_temp.txt"
    fi
}

# Function to cleanup
cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
    rm -f "$OUTPUT_DIR/files_list_raw.txt" "$OUTPUT_DIR/extensions_temp.txt"
}

# Main function
main() {
    # Parse command line arguments
    local export_txt=false
    local export_csv=false
    local export_json=false
    local show_tree=false
    local verbose=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--token)
                GITHUB_TOKEN="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --csv)
                export_csv=true
                shift
                ;;
            --json)
                export_json=true
                shift
                ;;
            --txt)
                export_txt=true
                shift
                ;;
            --show-tree)
                show_tree=true
                shift
                ;;
            --verbose|-v)
                verbose=true
                shift
                ;;
            --all)
                export_txt=true
                export_csv=true
                export_json=true
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                REPO_URL="$1"
                shift
                ;;
        esac
    done
    
    # Default to TXT if no export format specified
    if [[ "$export_txt" == false && "$export_csv" == false && "$export_json" == false ]]; then
        export_txt=true
    fi
    
    # Check dependencies
    if ! command -v git &> /dev/null; then
        print_error "git is required but not installed"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    # Parse repository URL
    if ! parse_repo_url "$REPO_URL"; then
        print_error "Invalid repository URL: $REPO_URL"
        print_error "Expected format: https://github.com/owner/repo or owner/repo"
        exit 1
    fi
    
    # Create output directory and convert to absolute path
    mkdir -p "$OUTPUT_DIR"
    OUTPUT_DIR=$(cd "$OUTPUT_DIR" && pwd)
    
    print_info "Starting repository scan..."
    print_info "Repository: $REPO_OWNER/$REPO_NAME"
    print_info "Output directory: $OUTPUT_DIR"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Clone repository
    if ! clone_repository; then
        exit 1
    fi
    
    # Show directory tree if requested
    [[ "$show_tree" == true ]] && show_directory_tree
    
    # Scan files
    scan_files
    
    # Export files
    [[ "$export_txt" == true ]] && export_to_txt
    [[ "$export_csv" == true ]] && export_to_csv
    [[ "$export_json" == true ]] && export_to_json
    
    # Generate summary
    generate_summary
    
    print_success "Repository scan completed successfully!"
}

# Run main function with all arguments
main "$@"