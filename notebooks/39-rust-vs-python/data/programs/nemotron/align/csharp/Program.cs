using System;
using System.IO;
using System.Text;

class Program {
    static void Main(string[] args) {
        string text = File.ReadAllText(args[0]);
        int pos = 0;
        int len = text.Length;

        void Skip() {
            while (pos < len) {
                char c = text[pos];
                if (c != ' ' && c != '\n' && c != '\r' && c != '\t' && c != '\f') break;
                pos++;
            }
        }

        string Next() {
            Skip();
            int start = pos;
            while (pos < len) {
                char c = text[pos];
                if (c == ' ' || c == '\n' || c == '\r' || c == '\t' || c == '\f') break;
                pos++;
            }
            return text.Substring(start, pos - start);
        }

        int NextInt() {
            Skip();
            bool neg = false;
            if (pos < len && text[pos] == '-') { neg = true; pos++; }
            int v = 0;
            while (pos < len && text[pos] >= '0' && text[pos] <= '9') {
                v = v * 10 + (text[pos] - '0');
                pos++;
            }
            return neg ? -v : v;
        }

        string alphabet = Next();
        int A = alphabet.Length;

        int[] charIndex = new int[26];
        for (int i = 0; i < 26; i++) charIndex[i] = -1;
        for (int i = 0; i < A; i++) charIndex[alphabet[i] - 'A'] = i;

        int[] ins = new int[A];
        int[] del = new int[A];
        for (int i = 0; i < A; i++) ins[i] = NextInt();
        for (int i = 0; i < A; i++) del[i] = NextInt();
        int[][] sub = new int[A][];
        for (int i = 0; i < A; i++) {
            sub[i] = new int[A];
            for (int j = 0; j < A; j++) sub[i][j] = NextInt();
        }

        int P = NextInt();

        int[] prev = new int[1];
        int[] cur = new int[1];
        int[] sIdx = new int[0];
        int[] tIdx = new int[0];
        int[] insT = new int[0];

        long total = 0;
        var sb = new StringBuilder();

        for (int pair = 0; pair < P; pair++) {
            string s = Next();
            string t = Next();
            int n = s.Length, m = t.Length;

            if (sIdx.Length < n) sIdx = new int[n];
            for (int i = 0; i < n; i++) sIdx[i] = charIndex[s[i] - 'A'];
            if (tIdx.Length < m) tIdx = new int[m];
            if (insT.Length < m) insT = new int[m];
            for (int j = 0; j < m; j++) {
                tIdx[j] = charIndex[t[j] - 'A'];
                insT[j] = ins[tIdx[j]];
            }

            if (prev.Length < m + 1) { prev = new int[m + 1]; cur = new int[m + 1]; }

            prev[0] = 0;
            for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j - 1];

            for (int i = 1; i <= n; i++) {
                int si = sIdx[i - 1];
                int delSi = del[si];
                int[] subRow = sub[si];
                cur[0] = prev[0] + delSi;
                for (int j = 1; j <= m; j++) {
                    int tj = tIdx[j - 1];
                    int up = prev[j] + delSi;
                    int left = cur[j - 1] + insT[j - 1];
                    int diag = prev[j - 1] + subRow[tj];
                    int best = up < left ? up : left;
                    cur[j] = diag < best ? diag : best;
                }
                int[] tmp = prev; prev = cur; cur = tmp;
            }

            int cost = prev[m];
            total += cost;
            sb.Append(cost);
            sb.Append('\n');
        }
        sb.Append("total ");
        sb.Append(total);
        sb.Append('\n');
        Console.Write(sb.ToString());
    }
}
