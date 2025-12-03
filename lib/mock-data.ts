export type QuestionId = "Q1" | "Q2" | "Q3" | "Q4" | "Q5" | "Q6";

export type PlagiarismCase = {
  id: string;
  questionId: QuestionId;
  studentA: string;
  studentB: string;
  similarity: number;
  clusterId: string;
  codeA: string;
  codeB: string;
};

export const professorTemplate = `#include <stdio.h>

int main(void) {
    int n;
    printf("Enter n: ");
    scanf("%d", &n);

    // TODO: implement solution

    return 0;
}
`;

export const plagiarismCases: PlagiarismCase[] = [
  {
    id: "case-q1-1",
    questionId: "Q1",
    studentA: "Alice Carter",
    studentB: "Brian Lee",
    similarity: 93,
    clusterId: "cluster-q1",
    codeA: `#include <stdio.h>

int sum_to_n(int n) {
    int i;
    int sum = 0;

    for (i = 1; i <= n; i++) {
        sum += i;
    }

    return sum;
}

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\n", sum_to_n(n));
    return 0;
}
`,
    codeB: `#include <stdio.h>

int sum(int limit) {
    int i;
    int result = 0;

    for (i = 1; i <= limit; ++i) {
        result = result + i;
    }

    return result;
}

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\n", sum(n));
    return 0;
}
`
  },
  {
    id: "case-q1-2",
    questionId: "Q1",
    studentA: "Alice Carter",
    studentB: "Diana Singh",
    similarity: 81,
    clusterId: "cluster-q1",
    codeA: `#include <stdio.h>

int sum_to_n(int n) {
    int i;
    int sum = 0;

    for (i = 1; i <= n; i++) {
        sum += i;
    }

    return sum;
}

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\n", sum_to_n(n));
    return 0;
}
`,
    codeB: `#include <stdio.h>

int add_series(int up_to) {
    int i;
    int total = 0;

    for (i = 1; i <= up_to; i++) {
        total += i;
    }

    return total;
}

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\n", add_series(n));
    return 0;
}
`
  },
  {
    id: "case-q2-1",
    questionId: "Q2",
    studentA: "Ethan Park",
    studentB: "Farah Ibrahim",
    similarity: 88,
    clusterId: "cluster-q2",
    codeA: `#include <stdio.h>

int factorial(int n) {
    if (n == 0) {
        return 1;
    }

    return n * factorial(n - 1);
}

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\n", factorial(n));
    return 0;
}
`,
    codeB: `#include <stdio.h>

int fact(int x) {
    if (x <= 1) {
        return 1;
    }

    return x * fact(x - 1);
}

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\n", fact(n));
    return 0;
}
`
  },
  {
    id: "case-q3-1",
    questionId: "Q3",
    studentA: "Brian Lee",
    studentB: "Hannah Zhou",
    similarity: 72,
    clusterId: "cluster-q3",
    codeA: `#include <stdio.h>

int is_prime(int n) {
    if (n <= 1) {
        return 0;
    }

    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) {
            return 0;
        }
    }

    return 1;
}
`,
    codeB: `#include <stdio.h>

int prime(int x) {
    if (x <= 1) {
        return 0;
    }

    for (int d = 2; d * d <= x; d++) {
        if (x % d == 0) {
            return 0;
        }
    }

    return 1;
}
`
  },
  {
    id: "case-q4-1",
    questionId: "Q4",
    studentA: "Carla Gomez",
    studentB: "Ivan Petrov",
    similarity: 91,
    clusterId: "cluster-q4",
    codeA: `#include <stdio.h>

void reverse(int *arr, int n) {
    int i = 0;
    int j = n - 1;
    while (i < j) {
        int tmp = arr[i];
        arr[i] = arr[j];
        arr[j] = tmp;
        i++;
        j--;
    }
}
`,
    codeB: `#include <stdio.h>

void reverse_array(int *array, int len) {
    int left = 0;
    int right = len - 1;
    while (left < right) {
        int temp = array[left];
        array[left] = array[right];
        array[right] = temp;
        left++;
        right--;
    }
}
`
  },
  {
    id: "case-q5-1",
    questionId: "Q5",
    studentA: "Diana Singh",
    studentB: "Michael Chen",
    similarity: 76,
    clusterId: "cluster-q5",
    codeA: `#include <stdio.h>

int max(int a, int b) {
    return a > b ? a : b;
}
`,
    codeB: `#include <stdio.h>

int maximum(int x, int y) {
    if (x > y) {
        return x;
    }
    return y;
}
`
  },
  {
    id: "case-q6-1",
    questionId: "Q6",
    studentA: "Alice Carter",
    studentB: "Ivan Petrov",
    similarity: 84,
    clusterId: "cluster-q6",
    codeA: `#include <stdio.h>

int gcd(int a, int b) {
    while (b != 0) {
        int t = b;
        b = a % b;
        a = t;
    }
    return a;
}
`,
    codeB: `#include <stdio.h>

int gcd_iter(int x, int y) {
    int t;
    while (y != 0) {
        t = y;
        y = x % y;
        x = t;
    }
    return x;
}
`
  }
];

export const dashboardStats = {
  totalStudents: 48,
  totalQuestions: 6,
  highRiskCases: plagiarismCases.filter((c) => c.similarity >= 85).length,
  averageSimilarity:
    plagiarismCases.reduce((acc, c) => acc + c.similarity, 0) /
    plagiarismCases.length
};

export const gradeDistribution = [
  { questionId: "Q1" as QuestionId, submissions: 42, highRisk: 5 },
  { questionId: "Q2" as QuestionId, submissions: 45, highRisk: 3 },
  { questionId: "Q3" as QuestionId, submissions: 40, highRisk: 2 },
  { questionId: "Q4" as QuestionId, submissions: 44, highRisk: 4 },
  { questionId: "Q5" as QuestionId, submissions: 41, highRisk: 3 },
  { questionId: "Q6" as QuestionId, submissions: 39, highRisk: 2 }
];

export const originalityStats = [
  {
    label: "Original",
    value: 84
  },
  {
    label: "Suspicious",
    value: 16
  }
];