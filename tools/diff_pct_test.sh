#!/usr/bin/env bash
#
# diff_pct_test.sh — regression test for tools/diff_pct.py
#
# Validates 3 fixture cases that the legacy line-level diff failed:
#   case 1: long markdown lines vs spoken-transcript short lines, same content
#           → expected diff_pct < 30 (was ~198% under legacy)
#   case 2: completely different topic
#           → expected diff_pct ≥ 60
#   case 3: orig + ~20% new content appended
#           → expected diff_pct 10-30
#
# Usage:
#   bash tools/diff_pct_test.sh
# Exit:
#   0 = all pass
#   1 = ≥1 failure
#
# Runs against whichever backend is installed (rapidfuzz preferred, difflib
# fallback). Both should pass these ranges — they're chosen to be wide
# enough to absorb backend-algorithm differences.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DIFF_PCT="$SCRIPT_DIR/diff_pct.py"

if [[ ! -f "$DIFF_PCT" ]]; then
  echo "❌ diff_pct.py not found at $DIFF_PCT" >&2
  exit 1
fi

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

PASS=0
FAIL=0

run_case() {
  local label="$1"
  local orig="$2"
  local new="$3"
  local min="$4"
  local max="$5"

  local stderr_out
  stderr_out=$(mktemp)
  local actual
  actual=$(python3 "$DIFF_PCT" "$orig" "$new" 2>"$stderr_out")
  local backend
  backend=$(grep -oE 'backend=[a-z]+' "$stderr_out" | head -1 || echo "backend=?")
  rm -f "$stderr_out"

  if (( actual >= min && actual <= max )); then
    echo "  ✓ $label: diff_pct=$actual ∈ [$min, $max]  ($backend)"
    PASS=$((PASS+1))
  else
    echo "  ✗ $label: diff_pct=$actual NOT in [$min, $max]  ($backend)"
    FAIL=$((FAIL+1))
  fi
}

echo ""
echo "=== Case 1: long markdown line vs spoken-transcript short lines, same content ==="

cat > "$TMP/case1_orig.md" <<'EOF'
# Video draft — review-meeting retro

"Noticed something recently"—all the reviewers say the same thing: your research is too old-fashioned.

But look closely: they're all citing reactions from 5 years ago. AI isn't new. What's new is that everyone collectively woke up this time.

**Level-up point**: while everyone chases new concepts, those who see the pattern first are already making money with tools.
EOF

cat > "$TMP/case1_shot.md" <<'EOF'
Noticed something recently
all the reviewers say the same thing
your research is too old-fashioned
but look closely
they're all citing
reactions from 5 years ago
AI isn't new
what's new is that this time
everyone collectively woke up
while everyone chases new concepts
those who see the pattern first
are already making money with tools
EOF

run_case "spoken-style line breaks, content preserved" \
  "$TMP/case1_orig.md" "$TMP/case1_shot.md" 0 30

echo ""
echo "=== Case 2: completely different topic ==="

cat > "$TMP/case2_orig.md" <<'EOF'
# AI anxiety

Lately AI models ship too fast, a new tool every week.
You just learned one, next week it's obsolete.
This anxiety is essentially tool anxiety, not ability anxiety.
What's truly constant is your problem-solving paradigm—pick the right problem, define the eval, close the loop.
EOF

cat > "$TMP/case2_shot.md" <<'EOF'
Today let's talk about my cat
Her name is Orange, a British Shorthair
loves to curl up on the windowsill in the sun
Every day when I get home from work
seeing her makes me forget all my worries
She stole my milk today
got caught, pretended nothing happened
Cats really are the most magical creatures
EOF

run_case "completely different topic" \
  "$TMP/case2_orig.md" "$TMP/case2_shot.md" 60 100

echo ""
echo "=== Case 3: orig + ~20% appended (outro / CTA scenario) ==="

# Realistic creator scenario: pre-shoot draft ~150 words, a ~30-word outro added when filming.
# delta / orig ≈ 20%, Levenshtein/max(orig,new) ≈ 16-20%
cat > "$TMP/case3_orig.md" <<'EOF'
# Video — on fatalism

I never believed in fate. Until I ran this tool—it made me film a video and predicted the traffic.
I tried to prove it wrong, told my audience hoping collective observation would shift the data. The data was accurate.
I didn't escape fate. I just moved from first-order to second-order—AI is observing the observer.
EOF

cat > "$TMP/case3_shot.md" <<'EOF'
I never believed in fate. Until I ran this tool—it made me film a video and predicted the traffic.
I tried to prove it wrong, told my audience hoping collective observation would shift the data. The data was accurate.
I didn't escape fate. I just moved from first-order to second-order—AI is observing the observer.
Right now, you seeing this line—is it out of curiosity, or just closing the algorithm's last move?
EOF

run_case "~20% appended outro" \
  "$TMP/case3_orig.md" "$TMP/case3_shot.md" 10 30

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [[ $FAIL -eq 0 ]]; then
  exit 0
else
  exit 1
fi
