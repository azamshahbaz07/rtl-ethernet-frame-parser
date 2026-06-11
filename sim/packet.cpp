#include "packet.hpp"

#include <cctype>
#include <fstream>
#include <stdexcept>

namespace {
std::string read_file(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("unable to open corpus: " + path);
    }
    return std::string((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
}

std::vector<std::string> object_texts(const std::string& text) {
    std::vector<std::string> objects;
    size_t cases_pos = text.find("\"cases\"");
    if (cases_pos == std::string::npos) {
        return objects;
    }
    size_t array_pos = text.find('[', cases_pos);
    if (array_pos == std::string::npos) {
        return objects;
    }
    int depth = 0;
    bool in_string = false;
    bool escape = false;
    size_t start = std::string::npos;
    for (size_t i = array_pos + 1; i < text.size(); ++i) {
        const char c = text[i];
        if (in_string) {
            if (escape) {
                escape = false;
            } else if (c == '\\') {
                escape = true;
            } else if (c == '"') {
                in_string = false;
            }
            continue;
        }
        if (c == '"') {
            in_string = true;
        } else if (c == '{') {
            if (depth == 0) {
                start = i;
            }
            ++depth;
        } else if (c == '}') {
            --depth;
            if (depth == 0 && start != std::string::npos) {
                objects.push_back(text.substr(start, i - start + 1));
                start = std::string::npos;
            }
        } else if (c == ']' && depth == 0) {
            break;
        }
    }
    return objects;
}

std::string string_field(const std::string& object, const std::string& key) {
    const std::string needle = "\"" + key + "\"";
    size_t pos = object.find(needle);
    if (pos == std::string::npos) {
        return "";
    }
    pos = object.find(':', pos);
    pos = object.find('"', pos);
    if (pos == std::string::npos) {
        return "";
    }
    size_t end = object.find('"', pos + 1);
    if (end == std::string::npos) {
        return "";
    }
    return object.substr(pos + 1, end - pos - 1);
}

double number_field(const std::string& object, const std::string& key, double fallback) {
    const std::string needle = "\"" + key + "\"";
    size_t pos = object.find(needle);
    if (pos == std::string::npos) {
        return fallback;
    }
    pos = object.find(':', pos);
    if (pos == std::string::npos) {
        return fallback;
    }
    ++pos;
    while (pos < object.size() && std::isspace(static_cast<unsigned char>(object[pos]))) {
        ++pos;
    }
    size_t end = pos;
    while (end < object.size() &&
           (std::isdigit(static_cast<unsigned char>(object[end])) || object[end] == '.')) {
        ++end;
    }
    return std::stod(object.substr(pos, end - pos));
}

std::vector<std::string> string_array_field(const std::string& object, const std::string& key) {
    std::vector<std::string> values;
    const std::string needle = "\"" + key + "\"";
    size_t pos = object.find(needle);
    if (pos == std::string::npos) {
        return values;
    }
    pos = object.find('[', pos);
    size_t end = object.find(']', pos);
    if (pos == std::string::npos || end == std::string::npos) {
        return values;
    }
    std::string body = object.substr(pos + 1, end - pos - 1);
    size_t scan = 0;
    while (true) {
        size_t open = body.find('"', scan);
        if (open == std::string::npos) {
            break;
        }
        size_t close = body.find('"', open + 1);
        if (close == std::string::npos) {
            break;
        }
        values.push_back(body.substr(open + 1, close - open - 1));
        scan = close + 1;
    }
    return values;
}

uint8_t hex_nibble(char c) {
    if (c >= '0' && c <= '9') {
        return static_cast<uint8_t>(c - '0');
    }
    if (c >= 'a' && c <= 'f') {
        return static_cast<uint8_t>(c - 'a' + 10);
    }
    if (c >= 'A' && c <= 'F') {
        return static_cast<uint8_t>(c - 'A' + 10);
    }
    throw std::runtime_error("invalid hex digit in corpus");
}

std::vector<uint8_t> parse_hex(const std::string& hex) {
    if ((hex.size() % 2) != 0) {
        throw std::runtime_error("frame_hex must contain an even number of digits");
    }
    std::vector<uint8_t> bytes;
    bytes.reserve(hex.size() / 2);
    for (size_t i = 0; i < hex.size(); i += 2) {
        bytes.push_back(static_cast<uint8_t>((hex_nibble(hex[i]) << 4) | hex_nibble(hex[i + 1])));
    }
    return bytes;
}
}  // namespace

std::vector<PacketCase> load_corpus(const std::string& path) {
    std::vector<PacketCase> cases;
    for (const std::string& object : object_texts(read_file(path))) {
        PacketCase c;
        c.name = string_field(object, "name");
        c.frame = parse_hex(string_field(object, "frame_hex"));
        c.tags = string_array_field(object, "tags");
        c.input_gap_prob = number_field(object, "input_gap_prob", 0.0);
        c.meta_stall_cycles = static_cast<int>(number_field(object, "meta_stall_cycles", 0.0));
        if (c.name.empty()) {
            throw std::runtime_error("corpus case is missing name");
        }
        cases.push_back(c);
    }
    return cases;
}
