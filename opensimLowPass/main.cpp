#include <Common/TimeSeriesTable.h>
#include <OpenSim/OpenSim.h>
#include <SimTKcommon/internal/BigMatrix.h>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

void load_data(const std::string &filename, std::vector<double> &times, std::vector<double> &signal) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }

    std::string line;
    getline(file, line); // Skip the header line

    double time, value;
    while (getline(file, line)) {
        // Create a stringstream to parse the line
        std::stringstream ss(line);
        
        // Read the time and value, handling any leading/trailing spaces
        char comma; // To handle the comma separating the values
        if (ss >> time >> comma >> value) {
            times.push_back(time);
            signal.push_back(value);
        } else {
            std::cerr << "Warning: Invalid line format or data: " << line << std::endl;
        }
    }

    // Check for EOF or other read errors
    if (file.eof()) {
        std::cout << "File read complete." << std::endl;
    } else {
        std::cerr << "Error reading data from file: " << filename << std::endl;
    }
}

void save_filtered_data(const std::string &filename,
                        const std::vector<double> &times,
                        const OpenSim::TimeSeriesTable &table) {
  std::cout << "Opening filename: " << filename << std::endl;
  std::ofstream file(filename);
  if (!file.is_open()) {
    throw std::runtime_error("Could not open file for writing: " + filename);
  }
  // Check that filtered_signal and times have the same size

  
  const auto &filtered_data = table.getDependentColumnAtIndex(0);
  file << "time,value\n";
  for (size_t i = 0; i < times.size(); ++i) {
    // std::cout << times[i] << "," << filtered_signal[i] << std::endl;
    const auto& time = times[i];
    const auto& index = table.getNearestRowIndexForTime(time);
    file << time << "," << filtered_data[index] << "\n";
  }
}

int main() {
  // Directories (Adjust according to your file structure)
  std::string data_dir = "../../data";
  std::string source_dir = data_dir + "/source";
  std::string results_dir = data_dir + "/results";

  try {
    // Load data
    std::vector<double> no_noise_times, no_noise_signal;
    std::vector<double> with_noise_times, with_noise_signal;

    std::cout << "Loading data from : " << source_dir << std::endl;
    load_data(source_dir + "/sine_wave_no_noise.txt", no_noise_times,
              no_noise_signal);

    load_data(source_dir + "/sine_wave_with_noise.txt", with_noise_times,
              with_noise_signal);

    // Compute sampling rate
    double sampling_rate = no_noise_times.size() /
                           (no_noise_times.back() - no_noise_times.front());
    std::cout << "Sampling rate: " << sampling_rate << " Hz" << std::endl;

    // Convert to OpenSim's TimeSeriesTable format
    SimTK::Matrix data(with_noise_signal.size(),1);
    for (size_t i=0; i< with_noise_signal.size(); i++){
      data(i,0) = with_noise_signal[i];
    }

    std::vector<std::string> labels = {"signal"};

    // Create TimeSeriesTable from time and signal
    const OpenSim::TimeSeriesTable table(with_noise_times,data,labels);
    // for (size_t i =0; i < table.getNumRows(); i++) {
    //   std::cout << table.getDependentColumnAtIndex(0) << std::endl;
    // }

    // Filtering using TableUtilities::filterLowpass
    std::vector<int> cutoff_frequencies = {3, 6, 12, 20};

    for (int cutoff : cutoff_frequencies) {
      OpenSim::TimeSeriesTable upd_table{table};
      // Filter the table using OpenSim's filterLowpass
      // const auto& processor = OpenSim::TableProcessor(table) |
      //                         OpenSim::TabOpLowPassFilter(cutoff);
      // processor.process();
      OpenSim::TableUtilities::filterLowpass(upd_table, cutoff,true);

      // Extract the filtered signal from the table
      // for (const auto val : table.getIndependentColumn()){
      //   std::cout << val << std::endl;
      // }

      // Generate file name for saving the results
      std::string filename =
          results_dir + "/opensim_results_" + std::to_string(cutoff) + "_hz.txt";
      save_filtered_data(filename, with_noise_times, upd_table);

      std::cout << "Filtered signal for cutoff " << cutoff
                << " Hz written to: " << filename << std::endl;
    }
    std::cout << "Filtering complete. Files written to: " << results_dir
              << std::endl;

  } catch (const std::exception &ex) {
    std::cerr << "Error: " << ex.what() << std::endl;
    return 1;
  }

  return EXIT_SUCCESS;
}
