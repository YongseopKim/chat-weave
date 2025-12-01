#!/bin/bash

# ChatWeave: 배치 IR 생성 스크립트
#
# 각 하위 디렉토리에서:
# 1. JSONL 파일들을 raw/ 디렉토리로 이동
# 2. ir/ 디렉토리 생성
# 3. Conversation IR 생성
#
# Usage: ./batch_build_ir.sh <directory>
# Example: ./batch_build_ir.sh ~/Downloads

set -e  # 에러 발생 시 중단

# 사용법 표시
if [ $# -eq 0 ]; then
  echo "Usage: $0 <directory>"
  echo ""
  echo "Process all subdirectories in the given directory:"
  echo "  1. Move JSONL files to subdirectory/raw/"
  echo "  2. Create subdirectory/ir/"
  echo "  3. Generate Conversation IR in subdirectory/ir/"
  echo ""
  echo "Example:"
  echo "  $0 ~/Downloads"
  echo "  $0 /path/to/sessions"
  exit 1
fi

# 디렉토리 인자 받기
target_dir="$1"

# 디렉토리 존재 확인
if [ ! -d "$target_dir" ]; then
  echo "Error: Directory not found: $target_dir"
  exit 1
fi

# 절대 경로로 변환
target_dir=$(cd "$target_dir" && pwd)

# 색상 정의 (출력용)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ChatWeave 일괄 처리 시작 ===${NC}"
echo -e "Target directory: ${target_dir}\n"

# 처리된 디렉토리 카운터
processed=0
skipped=0
failed=0

# 대상 디렉토리의 모든 하위 디렉토리 순회
for dir in "${target_dir}"/*/; do
  # 디렉토리가 실제로 존재하는지 확인
  if [ ! -d "$dir" ]; then
    continue
  fi

  dirname=$(basename "$dir")

  echo -e "${BLUE}[$(date +%H:%M:%S)] Processing: ${dirname}${NC}"

  # raw/ 디렉토리 경로
  raw_dir="${dir}raw/"

  # JSONL 파일 확인: 루트와 raw/ 둘 다 체크
  root_jsonl_count=$(find "$dir" -maxdepth 1 -name "*.jsonl" -type f 2>/dev/null | wc -l)
  raw_jsonl_count=0
  if [ -d "$raw_dir" ]; then
    raw_jsonl_count=$(find "$raw_dir" -maxdepth 1 -name "*.jsonl" -type f 2>/dev/null | wc -l)
  fi

  total_jsonl=$((root_jsonl_count + raw_jsonl_count))

  if [ "$total_jsonl" -eq 0 ]; then
    echo -e "${YELLOW}  ⊘ No JSONL files found, skipping${NC}\n"
    ((skipped++))
    continue
  fi

  # 1. raw/ 디렉토리 생성
  mkdir -p "$raw_dir"
  echo -e "  ${GREEN}✓${NC} Created/verified raw/ directory"

  # 2. JSONL 파일들을 raw/로 이동 (루트에 있는 경우만)
  if [ "$root_jsonl_count" -gt 0 ]; then
    echo -e "  Found ${root_jsonl_count} JSONL file(s) in root"
    moved=0
    for jsonl in "${dir}"*.jsonl; do
      if [ -f "$jsonl" ]; then
        filename=$(basename "$jsonl")
        mv "$jsonl" "${raw_dir}${filename}"
        echo -e "  ${GREEN}→${NC} Moved: ${filename}"
        ((moved++))
      fi
    done
    if [ "$moved" -gt 0 ]; then
      echo -e "  ${GREEN}✓${NC} Moved ${moved} JSONL file(s) to raw/"
    fi
  elif [ "$raw_jsonl_count" -gt 0 ]; then
    echo -e "  ${BLUE}ℹ${NC} Found ${raw_jsonl_count} JSONL file(s) already in raw/ (skipping move)"
  fi

  # 3. ir/ 디렉토리 생성
  ir_dir="${dir}ir/"
  mkdir -p "$ir_dir"
  echo -e "  ${GREEN}✓${NC} Created/verified ir/ directory"

  # 4. Conversation IR 생성
  echo -e "  ${BLUE}⚙${NC} Generating Conversation IR..."

  if chatweave build-ir "$raw_dir" \
      --output "$ir_dir" \
      --step conversation \
      --quiet; then
    echo -e "  ${GREEN}✓${NC} Conversation IR generated successfully"
    ((processed++))
  else
    echo -e "  ${RED}✗${NC} Failed to generate Conversation IR"
    ((failed++))
  fi

  echo ""
done

# 최종 요약
echo -e "${BLUE}=== 처리 완료 ===${NC}"
echo -e "  ${GREEN}성공:${NC} ${processed}개 디렉토리"
echo -e "  ${YELLOW}건너뜀:${NC} ${skipped}개 디렉토리 (JSONL 없음)"
if [ "$failed" -gt 0 ]; then
  echo -e "  ${RED}실패:${NC} ${failed}개 디렉토리"
fi
echo ""
