#include <OpenSim/Common/C3DFileAdapter.h>
#include <OpenSim/Common/STOFileAdapter.h>
#include <OpenSim/Common/TRCFileAdapter.h>

#include <SimTKcommon/SmallMatrix.h>
#include <sstream>

#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

// Rotation from marker space to OpenSim space (y is up)
// This is the rotation for the kuopio gait dataset
const SimTK::Vec3 rotations(-SimTK::Pi / 2, SimTK::Pi / 2, 0);

void rotateMarkerTable(OpenSim::TimeSeriesTableVec3 &table,
                       const SimTK::Rotation_<double> &rotationMatrix) {
  const SimTK::Rotation R_XG = rotationMatrix;

  int nc = int(table.getNumColumns());
  size_t nt = table.getNumRows();

  for (size_t i = 0; i < nt; ++i) {
    auto row = table.updRowAtIndex(i);
    for (int j = 0; j < nc; ++j) {
      row[j] = R_XG * row[j];
    }
  }
  return;
}

template <typename C> 
std::string vectorToString(const C &vec) {
  std::ostringstream oss;
  oss << "{";
  for (size_t i = 0; i < vec.size(); ++i) {
    oss << vec[i];
    if (i < vec.size() - 1)
      oss << ",";
  }
  oss << "}";
  std::string input = oss.str();
  // Strip new lines
  input.erase(std::remove(input.begin(), input.end(), '\n'), input.end());
  return input;
}

std::string serializeValue(const SimTK::AbstractValue &value,
                           const std::string &key) {
  std::string output = value.getValueAsString();
  const auto &type_name = value.getTypeName();
  // std::cout << type << " ; " << type_name << std::endl;
  if (key == "CalibrationMatrices" || key == "Corners" || key == "Origins") {
    output =
        vectorToString(value.getValue<std::vector<SimTK::Matrix_<double>>>());
  } else if (key == "Types") {
    output = vectorToString(value.getValue<std::vector<unsigned>>());
  } else if (key == "events") {
    // output = vectorToString(value.getValue<std::vector<OpenSim::Event>>());
  }
  else if (type_name == "std::string") {
    // default condition if it's a normal type
    output = value.getValue<std::string>();
  }
  return output;
}

namespace fs = std::filesystem;
void processC3DFile(const fs::path &filename, const fs::path &resultPath) {
  std::cout << "---Starting Processing: " << filename << std::endl;
  try {
    OpenSim::C3DFileAdapter c3dFileAdapter{};
    auto tables = c3dFileAdapter.read(filename);
    auto forces = tables.at("forces");
    const auto meta_data = forces->getTableMetaData();
    for (auto key : meta_data.getKeys()) {
      const auto &value = meta_data.getValueForKey(key);
      const auto &result = serializeValue(value,key);
      std::cout << key << " = " << result << std::endl;
      // Massive chungus ?! - why does it have to be removed first
      forces->updTableMetaData().removeValueForKey(key);
      forces->updTableMetaData().setValueForKey(key,result);
      // std:: cout << value.getValueAsString() << std::endl;
    }
    std::shared_ptr<OpenSim::TimeSeriesTableVec3> marker_table =
        c3dFileAdapter.getMarkersTable(tables);
    std::shared_ptr<OpenSim::TimeSeriesTableVec3> force_table =
        c3dFileAdapter.getForcesTable(tables);
    std::shared_ptr<OpenSim::TimeSeriesTable> analog_table =
        c3dFileAdapter.getAnalogDataTable(tables);

    std::filesystem::path baseDir = resultPath;

    // Create directories if they don't exist
    try {
      if (std::filesystem::create_directories(baseDir)) {
        std::cout << "Directories created: " << baseDir << std::endl;
      }
    } catch (const std::filesystem::filesystem_error &e) {
      std::cerr << "Error creating directories: " << e.what() << std::endl;
    }

    std::string pathStr = filename.stem().string();
    // sanatize output
    std::replace(pathStr.begin(), pathStr.end(), ' ', '_');
    std::replace(pathStr.begin(), pathStr.end(), '\\', '_');
    std::cout << "   Path after replacement : " << pathStr << std::endl;

    const std::string marker_file = baseDir / (pathStr + "_markers.trc");
    const std::string forces_file = baseDir / (pathStr + "_grfs.sto");
    const std::string analogs_file = baseDir / (pathStr + "_analog.sto");

    // Write marker locations
    marker_table->updTableMetaData().setValueForKey("Units", std::string{"mm"});
    OpenSim::TRCFileAdapter trc_adapter{};
    const SimTK::Rotation sensorToOpenSim = SimTK::Rotation(
        SimTK::BodyOrSpaceType::SpaceRotationSequence, rotations[0],
        SimTK::XAxis, rotations[1], SimTK::YAxis, rotations[2], SimTK::ZAxis);
    rotateMarkerTable(*marker_table, sensorToOpenSim);

    trc_adapter.write(*marker_table, marker_file);
    std::cout << "\tWrote '" << marker_file << std::endl;

    // Write forces and analog
    OpenSim::STOFileAdapter sto_adapter{};
    sto_adapter.write((force_table->flatten()), forces_file);
    std::cout << "\tWrote'" << forces_file << std::endl;
    sto_adapter.write(*analog_table, analogs_file);
    std::cout << "\tWrote'" << analogs_file << std::endl;
  } catch (...) {
    std::cout << "Error in processing C3D File: " << filename << std::endl;
  }
  std::cout << "---Ending Processing: " << filename << std::endl;
}

int main(int argc, char *argv[]) {
  std::chrono::steady_clock::time_point begin =
      std::chrono::steady_clock::now();
  if (argc < 3) {
    std::cerr << "Usage: " << argv[0] << " <file_path> <output_path>"
              << std::endl;
    return 1;
  }

  fs::path filePath = argv[1];
  if (!fs::exists(filePath)) {
    std::cerr << "The provided path is not valid." << std::endl;
    return 1;
  }

  fs::path outputPath = argv[2];

  processC3DFile(filePath, outputPath);
  std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
  std::cout << "Runtime = "
            << std::chrono::duration_cast<std::chrono::microseconds>(end -
                                                                     begin)
                   .count()
            << "[µs]" << std::endl;
  std::cout << "Results Saved to directory: " << outputPath << std::endl;
  std::cout << "Finished Running without Error!" << std::endl;
  return 0;
}
