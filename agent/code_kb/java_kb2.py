"""Java snippets for the SADAH v6 tasks (part 1). Java 17+."""

SNIPPETS = {
    "inheritance": r'''
class Animal {
    protected String name;
    Animal(String name) { this.name = name; }
    String speak() { return "..."; }
}

class Dog extends Animal {               // Dog inherits from Animal
    Dog(String name) { super(name); }
    @Override
    String speak() { return name + ": Woof!"; }
}

// in main:
System.out.println(new Dog("Rex").speak());''',
    "interface": r'''
interface Shape {
    double area();
}

record Circle(double r) implements Shape {
    public double area() { return Math.PI * r * r; }
}

// in main:
Shape s = new Circle(2);
System.out.println(s.area());''',
    "lambda": r'''
import java.util.*;
import java.util.function.*;

Function<Integer, Integer> square = x -> x * x;
System.out.println(square.apply(5));          // 25

List<String> names = new ArrayList<>(List.of("Sara", "Ali", "Mohammed"));
names.sort((a, b) -> a.length() - b.length());
System.out.println(names);''',
    "map_filter": r'''
import java.util.*;
import java.util.stream.*;

List<Integer> nums = List.of(1, 2, 3, 4, 5, 6);
List<Integer> evens = nums.stream().filter(n -> n % 2 == 0).collect(Collectors.toList());
List<Integer> squares = nums.stream().map(n -> n * n).collect(Collectors.toList());
System.out.println(evens + " " + squares);''',
    "set_ops": r'''
import java.util.*;

Set<Integer> a = new HashSet<>(List.of(1, 2, 3, 4));
Set<Integer> b = new HashSet<>(List.of(3, 4, 5));
Set<Integer> union = new HashSet<>(a);  union.addAll(b);
Set<Integer> inter = new HashSet<>(a);  inter.retainAll(b);
System.out.println(union + " " + inter);''',
    "recursion": r'''
static long factorial(int n) {
    if (n <= 1) return 1;          // base case
    return n * factorial(n - 1);
}

// in main:
System.out.println(factorial(5));   // 120''',
    "binary_search": r'''
static int binarySearch(int[] items, int target) {
    int lo = 0, hi = items.length - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (items[mid] == target) return mid;
        if (items[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}

// in main:
System.out.println(binarySearch(new int[]{1, 3, 5, 7, 9, 11}, 7));   // 3''',
    "quicksort": r'''
static void quicksort(int[] a, int lo, int hi) {
    if (lo >= hi) return;
    int pivot = a[hi], i = lo;
    for (int j = lo; j < hi; j++) {
        if (a[j] < pivot) { int t = a[i]; a[i] = a[j]; a[j] = t; i++; }
    }
    int t = a[i]; a[i] = a[hi]; a[hi] = t;
    quicksort(a, lo, i - 1);
    quicksort(a, i + 1, hi);
}

// in main:
int[] data = {5, 2, 9, 1, 7, 3};
quicksort(data, 0, data.length - 1);
System.out.println(java.util.Arrays.toString(data));''',
    "stack_queue": r'''
import java.util.*;

Deque<Integer> stack = new ArrayDeque<>();
stack.push(1); stack.push(2);
System.out.println(stack.pop());      // 2  (last in, first out)

Queue<String> queue = new LinkedList<>();
queue.add("a"); queue.add("b");
System.out.println(queue.poll());     // a  (first in, first out)''',
    "string_format": r'''
String name = "Sara";
double score = 93.456;
System.out.println(String.format("%s scored %.1f%%", name, score));
System.out.printf("%-10s|%10s|%n", "left", "right");
System.out.println("%s has %d points".formatted(name, 42));''',
    "regex": r'''
import java.util.regex.*;

String email = "user@example.com";
System.out.println(email.matches("[\\w.+-]+@[\\w-]+\\.[\\w.]+"));   // true

Matcher m = Pattern.compile("05\\d{8}").matcher("Call 0551234567 or 0569876543");
while (m.find()) System.out.println(m.group());''',
    "threads": r'''
Runnable work = () -> {
    try { Thread.sleep(1000); } catch (InterruptedException e) { return; }
    System.out.println(Thread.currentThread().getName() + " done");
};
Thread t1 = new Thread(work), t2 = new Thread(work);
t1.start(); t2.start();
t1.join();  t2.join();      // main() must declare: throws InterruptedException''',
    "async_code": r'''
import java.util.concurrent.*;

CompletableFuture<Integer> a = CompletableFuture.supplyAsync(() -> 10);
CompletableFuture<Integer> b = CompletableFuture.supplyAsync(() -> 20);
int total = a.thenCombine(b, Integer::sum).join();
System.out.println(total);   // 30''',
}
