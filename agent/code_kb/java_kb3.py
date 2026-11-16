"""Java snippets for the SADAH v6 tasks (part 2). Java 17+."""

SNIPPETS = {
    "unit_test": r'''
// JUnit 5 (add org.junit.jupiter:junit-jupiter to your build)
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class CalculatorTest {
    static int add(int a, int b) { return a + b; }

    @Test
    void addsTwoNumbers() {
        assertEquals(5, add(2, 3));
    }
}''',
    "enum": r'''
enum Color { RED, GREEN, BLUE }

// in main:
Color c = Color.GREEN;
System.out.println(c + " " + c.ordinal());
for (Color each : Color.values()) System.out.println(each);''',
    "palindrome": r'''
static boolean isPalindrome(String text) {
    String clean = text.replaceAll("[^A-Za-z0-9]", "").toLowerCase();
    return new StringBuilder(clean).reverse().toString().equals(clean);
}

// in main:
System.out.println(isPalindrome("Racecar"));   // true''',
    "fibonacci_code": r'''
long a = 0, b = 1;
for (int i = 0; i < 10; i++) {
    System.out.print(a + " ");
    long next = a + b;
    a = b;
    b = next;
}''',
    "prime_check": r'''
static boolean isPrime(int n) {
    if (n < 2) return false;
    for (int i = 2; (long) i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

// in main:
for (int n = 0; n < 30; n++) if (isPrime(n)) System.out.print(n + " ");''',
    "matrix": r'''
int[][] a = {{1, 2}, {3, 4}};
int[][] b = {{5, 6}, {7, 8}};
int[][] c = new int[2][2];
for (int i = 0; i < 2; i++)
    for (int j = 0; j < 2; j++)
        for (int k = 0; k < 2; k++)
            c[i][j] += a[i][k] * b[k][j];
System.out.println(java.util.Arrays.deepToString(c));   // [[19, 22], [43, 50]]''',
    "user_input": r'''
import java.util.Scanner;

Scanner in = new Scanner(System.in);
System.out.print("What's your name? ");
String name = in.nextLine();
System.out.print("Your age: ");
int age = in.nextInt();
System.out.println("Hello " + name + ", next year you will be " + (age + 1));''',
    "linked_list": r'''
class Node {
    int value;
    Node next;
    Node(int value, Node next) { this.value = value; this.next = next; }
}

// in main:
Node head = null;
for (int v : new int[]{3, 2, 1}) head = new Node(v, head);
for (Node n = head; n != null; n = n.next) System.out.print(n.value + " ");   // 1 2 3
// built-in: java.util.LinkedList<Integer> list = new java.util.LinkedList<>();''',
    "count_words": r'''
import java.util.*;

String text = "the cat and the hat and the bat";
Map<String, Integer> counts = new TreeMap<>();
for (String w : text.split("\\s+")) counts.merge(w, 1, Integer::sum);
System.out.println(text.split("\\s+").length + " words: " + counts);''',
    "custom_exception": r'''
class InsufficientFundsException extends Exception {
    InsufficientFundsException(String msg) { super(msg); }
}

static int withdraw(int balance, int amount) throws InsufficientFundsException {
    if (amount > balance) throw new InsufficientFundsException("need " + (amount - balance) + " more");
    return balance - amount;
}

// in main:
try { withdraw(100, 150); }
catch (InsufficientFundsException e) { System.out.println("Error: " + e.getMessage()); }''',
    "csv_file": r'''
import java.nio.file.*;
import java.util.*;

Path file = Path.of("people.csv");
Files.write(file, List.of("name,age", "Sara,30", "Ali,25"));
for (String line : Files.readAllLines(file).subList(1, 3)) {
    String[] cols = line.split(",");
    System.out.println(cols[0] + " is " + cols[1]);
}   // main() must declare: throws Exception''',
    "database": r'''
// needs the sqlite-jdbc driver (org.xerial:sqlite-jdbc)
import java.sql.*;

try (Connection con = DriverManager.getConnection("jdbc:sqlite:app.db")) {
    con.createStatement().execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)");
    PreparedStatement ins = con.prepareStatement("INSERT INTO users (name) VALUES (?)");
    ins.setString(1, "Sara");
    ins.executeUpdate();
    ResultSet rs = con.createStatement().executeQuery("SELECT id, name FROM users");
    while (rs.next()) System.out.println(rs.getInt("id") + " " + rs.getString("name"));
}''',
}
