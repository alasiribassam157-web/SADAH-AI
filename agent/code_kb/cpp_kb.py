"""C++ snippets (C++17). Statements go inside main() with #include <iostream> and <string>."""
SNIPPETS = {
    "hello_world": r'''
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}''',
    "variables": r'''
std::string name = "Sara";
int age = 25;
double pi = 3.14;
bool isActive = true;
std::cout << name << " " << age << " " << pi << " " << isActive << std::endl;''',
    "if_else": r'''
int age = 20;
if (age >= 18) {
    std::cout << "Adult\n";
} else if (age >= 13) {
    std::cout << "Teen\n";
} else {
    std::cout << "Child\n";
}''',
    "for_loop": r'''
#include <vector>

for (int i = 0; i < 5; i++) {
    std::cout << i << "\n";
}

std::vector<std::string> fruits = {"apple", "banana"};
for (const auto& fruit : fruits) {
    std::cout << fruit << "\n";
}''',
    "while_loop": r'''
int count = 0;
while (count < 5) {
    std::cout << count << "\n";
    count++;
}''',
    "function": r'''
int add(int a, int b) {
    return a + b;
}

// inside main:
std::cout << add(2, 3) << std::endl; // 5''',
    "list": r'''
#include <vector>

std::vector<int> nums = {3, 1, 2};
nums.push_back(4);
std::cout << nums[0] << " " << nums.size() << std::endl; // 3 4''',
    "dict": r'''
#include <map>

std::map<std::string, int> ages = {{"Ali", 30}, {"Sara", 25}};
ages["Omar"] = 22;
for (const auto& [name, age] : ages) {
    std::cout << name << " " << age << "\n";
}''',
    "class": r'''
class Person {
public:
    explicit Person(std::string name) : name_(std::move(name)) {}
    std::string greet() const { return "Hi, I'm " + name_; }
private:
    std::string name_;
};

// inside main:
std::cout << Person("Ali").greet() << std::endl;''',
    "read_file": r'''
#include <fstream>
#include <sstream>

std::ifstream file("data.txt");
std::stringstream buffer;
buffer << file.rdbuf();
std::cout << buffer.str();''',
    "write_file": r'''
#include <fstream>

std::ofstream file("out.txt");
file << "Hello file\n";''',
    "reverse_string": r'''
#include <algorithm>

std::string text = "hello";
std::reverse(text.begin(), text.end());
std::cout << text << std::endl; // olleh''',
    "sort_list": r'''
#include <algorithm>
#include <vector>

std::vector<int> nums = {5, 2, 9, 1};
std::sort(nums.begin(), nums.end());
for (int n : nums) std::cout << n << " "; // 1 2 5 9''',
    "try_catch": r'''
#include <stdexcept>

try {
    throw std::runtime_error("something failed");
} catch (const std::exception& e) {
    std::cout << "Error: " << e.what() << std::endl;
}''',
    "http_request": r'''
// C++ has no built-in HTTP client; a popular library is cpr (github.com/libcpr/cpr).
#include <cpr/cpr.h>

cpr::Response r = cpr::Get(cpr::Url{"https://api.github.com"});
std::cout << r.status_code << std::endl;''',
    "json_parse": r'''
// Popular choice: nlohmann/json (single header, github.com/nlohmann/json).
#include <nlohmann/json.hpp>

auto data = nlohmann::json::parse(R"({"name": "Ali", "age": 30})");
std::cout << data["name"].get<std::string>() << std::endl; // Ali''',
    "random_number": r'''
#include <random>

std::mt19937 gen(std::random_device{}());
std::uniform_int_distribution<int> dist(1, 100);
std::cout << dist(gen) << std::endl; // 1..100''',
    "current_date": r'''
#include <chrono>
#include <ctime>

std::time_t now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
std::cout << std::ctime(&now);''',
    "split_string": r'''
#include <sstream>
#include <vector>

std::stringstream ss("a,b,c");
std::string part;
std::vector<std::string> parts;
while (std::getline(ss, part, ',')) parts.push_back(part);''',
    "sum_max": r'''
#include <algorithm>
#include <numeric>
#include <vector>

std::vector<int> nums = {4, 8, 15};
int sum = std::accumulate(nums.begin(), nums.end(), 0);
int mx = *std::max_element(nums.begin(), nums.end());
std::cout << sum << " " << mx << std::endl; // 27 15''',
}
