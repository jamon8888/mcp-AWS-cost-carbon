import os
import pandas as pd
from typing import Dict, Optional, Union, List

class DataLoader:
    """Unified data loading for all calculators"""
    
    def __init__(self, data_dir: str = "data", mock_mode: bool = False):
        self.base_data_dir = data_dir
        self.mock_mode = mock_mode
        self.data_dir = os.path.join("mock") if mock_mode else self.base_data_dir
        if mock_mode and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"Created mock data directory: {self.data_dir}")
        elif not os.path.exists(self.data_dir):
             # Fallback to base data dir if specified doesn't exist (even in non-mock)
             print(f"Warning: Data directory {self.data_dir} not found. Falling back to {self.base_data_dir}")
             self.data_dir = self.base_data_dir
             if not os.path.exists(self.data_dir):
                 os.makedirs(self.data_dir) # Create base if it also doesn't exist
                 print(f"Created base data directory: {self.data_dir}")

        # Cache for loaded data
        self._cache = {}
    
    def load_csv(self, filename: str, index_col: Optional[str] = None) -> pd.DataFrame:
        """
        Load a CSV file into a pandas DataFrame
        
        Args:
            filename: Name of the CSV file
            index_col: Column to use as index
            
        Returns:
            DataFrame with loaded data
        """
        cache_key = f"{self.data_dir}:{filename}:{index_col}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        file_path = os.path.join(self.data_dir, filename)
        try:
            # Ensure the directory exists before trying to read
            if not os.path.exists(os.path.dirname(file_path)):
                 os.makedirs(os.path.dirname(file_path))
                 print(f"Created directory for data file: {os.path.dirname(file_path)}")

            if not os.path.exists(file_path):
                 print(f"Warning: Data file not found at {file_path}. Returning empty DataFrame.")
                 # Optionally, create a dummy file if in mock mode?
                 # if self.mock_mode:
                 #    pd.DataFrame().to_csv(file_path, index=False) # Example: create empty
                 return pd.DataFrame()

            df = pd.read_csv(file_path)
            if index_col and index_col in df.columns:
                df = df.set_index(index_col)
            self._cache[cache_key] = df
            return df
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            # Attempt to load from base directory as a fallback if in mock mode?
            if self.mock_mode and self.data_dir != self.base_data_dir:
                 print(f"Attempting fallback load from {self.base_data_dir}")
                 base_file_path = os.path.join(self.base_data_dir, filename)
                 try:
                     df = pd.read_csv(base_file_path)
                     if index_col and index_col in df.columns:
                         df = df.set_index(index_col)
                     self._cache[cache_key] = df # Cache it even if loaded from base
                     return df
                 except Exception as e_base:
                     print(f"Fallback load failed from {base_file_path}: {str(e_base)}")

            return pd.DataFrame()
    
    def load_region_data(self, data_type: str) -> Dict[str, Union[float, str]]:
        """
        Load region-specific data
        
        Args:
            data_type: Type of data (carbon_intensity, pue, water_usage, water_stress)
            
        Returns:
            Dictionary mapping regions to values
        """
        filename_map = {
            "carbon_intensity": "region_carbon_intensity.csv",
            "pue": "region_pue.csv",
            "water_usage": "region_water_usage.csv",
            "water_stress": "region_water_stress.csv"
        }
        
        if data_type not in filename_map:
            return {}
            
        df = self.load_csv(filename_map[data_type])
        if df.empty:
            print(f"Warning: Empty dataframe loaded for {data_type} from {filename_map[data_type]}. Returning empty dict.")
            # Optionally create mock data if in mock mode and file was missing
            if self.mock_mode and not os.path.exists(os.path.join(self.data_dir, filename_map[data_type])):
                self._create_mock_region_data(data_type, filename_map[data_type])
                # Retry loading after creating mock data
                df = self.load_csv(filename_map[data_type])
                if df.empty: # Still empty after mock creation? Problem.
                    return {}

        # Convert to dictionary
        if data_type == "water_stress":
            return dict(zip(df["region"], df["water_stress_level"]))
        else:
            value_col = df.columns[1]  # Assume second column has values
            return dict(zip(df["region"], df[value_col]))
    
    def load_model_data(self, data_type: str) -> Dict[str, Dict[str, float]]:
        """
        Load model-specific data
        
        Args:
            data_type: Type of data (energy_consumption, training_footprint)
            
        Returns:
            Nested dictionary mapping models to metrics
        """
        filename_map = {
            "energy_consumption": "model_energy_consumption.csv",
            "training_footprint": "model_training_footprint.csv"
        }
        
        if data_type not in filename_map:
            return {}
            
        df = self.load_csv(filename_map[data_type])
        if df.empty:
            print(f"Warning: Empty dataframe loaded for {data_type} from {filename_map[data_type]}. Returning empty dict.")
             # Optionally create mock data if in mock mode and file was missing
            if self.mock_mode and not os.path.exists(os.path.join(self.data_dir, filename_map[data_type])):
                self._create_mock_model_data(data_type, filename_map[data_type])
                # Retry loading after creating mock data
                df = self.load_csv(filename_map[data_type])
                if df.empty: # Still empty after mock creation? Problem.
                    return {}

        # Convert to nested dictionary
        result = {}
        for _, row in df.iterrows():
            model_id = row["model_id"]
            result[model_id] = row.drop("model_id").to_dict()
            
        return result 

    def _create_mock_region_data(self, data_type: str, filename: str):
        """Creates dummy region data if in mock mode and file is missing."""
        file_path = os.path.join(self.data_dir, filename)
        print(f"Creating mock data file: {file_path}")
        mock_data = []
        if data_type == "carbon_intensity":
            mock_data = [["us-east-1", 400.0], ["eu-west-1", 250.0]]
            cols = ["region", "carbon_intensity_gco2e_kwh"]
        elif data_type == "pue":
             mock_data = [["us-east-1", 1.15], ["eu-west-1", 1.12]]
             cols = ["region", "pue"]
        elif data_type == "water_usage":
             mock_data = [["us-east-1", 0.7], ["eu-west-1", 0.5]]
             cols = ["region", "water_usage_l_kwh"]
        elif data_type == "water_stress":
             mock_data = [["us-east-1", "Medium"], ["eu-west-1", "Low"]]
             cols = ["region", "water_stress_level"]

        if mock_data:
            pd.DataFrame(mock_data, columns=cols).to_csv(file_path, index=False)

    def _create_mock_model_data(self, data_type: str, filename: str):
        """Creates dummy model data if in mock mode and file is missing."""
        file_path = os.path.join(self.data_dir, filename)
        print(f"Creating mock data file: {file_path}")
        mock_data = []
        if data_type == "energy_consumption":
            mock_data = [
                ["claude-3-opus", 0.06, 0.18],
                ["gpt-4-turbo", 0.05, 0.15]
            ]
            cols = ["model_id", "input_kwh_per_million_tokens", "output_kwh_per_million_tokens"]
        elif data_type == "training_footprint":
             mock_data = [
                ["claude-3-opus", 50000 * 1000, 1e12], # 50k kgCO2e -> gCO2e
                ["gpt-4-turbo", 78000 * 1000, 1.5e12]  # 78k kgCO2e -> gCO2e
            ]
             cols = ["model_id", "total_emissions_gco2e", "expected_inferences"]

        if mock_data:
             pd.DataFrame(mock_data, columns=cols).to_csv(file_path, index=False) 