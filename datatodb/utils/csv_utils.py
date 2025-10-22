import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class CSVUtils:
    """Utility class for writing data to CSV files locally."""

    def __init__(self, output_dir: str = 'data'):
        """
        Initialize CSVUtils with an output directory.

        Args:
            output_dir: Directory where CSV files will be stored (default: 'data')
        """
        self.output_dir = output_dir
        self._ensure_output_directory()

    def _ensure_output_directory(self):
        """Create the output directory if it doesn't exist."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
        """
        Flatten nested dictionaries for CSV export.

        Args:
            data: Dictionary to flatten
            parent_key: Prefix for nested keys
            separator: Separator between parent and child keys

        Returns:
            Flattened dictionary
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, separator).items())
            elif isinstance(value, list):
                # Convert lists to string representation
                items.append((new_key, str(value)))
            else:
                items.append((new_key, value))

        return dict(items)

    def write_to_csv(self, data: List[Dict[str, Any]], filename: str, flatten: bool = True) -> str:
        """
        Write data to a CSV file.

        Args:
            data: List of dictionaries containing the data
            filename: Name of the CSV file (without extension)
            flatten: Whether to flatten nested dictionaries (default: True)

        Returns:
            Full path to the created CSV file
        """
        if not data:
            print(f"Warning: No data to write to {filename}.csv")
            return ""

        # Add timestamp to filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"{filename}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, csv_filename)

        # Flatten data if requested
        if flatten:
            processed_data = [self._flatten_dict(item) for item in data]
        else:
            processed_data = data

        # Get all unique keys from all dictionaries
        fieldnames = set()
        for item in processed_data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)

        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_data)

        print(f"Data written to: {filepath}")
        return filepath

    def append_to_csv(self, data: List[Dict[str, Any]], filepath: str, flatten: bool = True):
        """
        Append data to an existing CSV file.

        Args:
            data: List of dictionaries containing the data
            filepath: Full path to the CSV file
            flatten: Whether to flatten nested dictionaries (default: True)
        """
        if not data:
            print(f"Warning: No data to append to {filepath}")
            return

        # Flatten data if requested
        if flatten:
            processed_data = [self._flatten_dict(item) for item in data]
        else:
            processed_data = data

        # Check if file exists
        file_exists = os.path.isfile(filepath)

        if file_exists:
            # Read existing fieldnames
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
        else:
            # Get all unique keys from all dictionaries
            fieldnames = set()
            for item in processed_data:
                fieldnames.update(item.keys())
            fieldnames = sorted(fieldnames)

        # Append to CSV
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerows(processed_data)

        print(f"Data appended to: {filepath}")

    def get_latest_csv(self, prefix: str) -> str:
        """
        Get the path to the most recent CSV file with a given prefix.

        Args:
            prefix: Filename prefix to search for

        Returns:
            Full path to the most recent CSV file, or empty string if not found
        """
        csv_files = list(Path(self.output_dir).glob(f"{prefix}_*.csv"))

        if not csv_files:
            return ""

        # Sort by modification time and return the most recent
        latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
        return str(latest_file)
