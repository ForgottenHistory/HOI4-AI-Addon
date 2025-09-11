#!/bin/bash
echo "========================================"
echo "  Extract Character Names from HOI4"
echo "========================================"
echo
echo "This will extract character names from your HOI4 locale files"
echo "and update the personality system with fresh names."
echo
python3 name_extractor.py
echo
echo "✓ Name extraction complete!"
echo "The personality system now has updated character names."
echo
echo "========================================"