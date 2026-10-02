## Team Git Workflow

Each team member works in their **own branch**.

⚠️ Do not develop directly in the `main` branch.

The `main` branch should contain only stable and reviewed code.

---

## 1. Clone the repository

Open a terminal in the folder where you want to store the project.

```bash
git clone https://github.com/Gerokichi/Smart-School-Environment.git
```

Enter the project directory:

```bash
cd Smart-School-Environment
```

---

## 2. Create your personal branch

Each team member should create a branch using their GitHub username or name.

Example:

```bash
git switch -c your-name
```

For example:

```bash
git switch -c john
```

Then push the branch to GitHub:

```bash
git push -u origin your-name
```

This only needs to be done once.

After that, your branch will also appear on GitHub.

---

## 3. Check which branch you are currently using

Before changing any files, check your current branch:

```bash
git branch
```

Example:

```text
  main
* john
```

The `*` shows your current branch.

Make sure you are working in **your own branch**, not `main`.

To switch to your branch:

```bash
git switch your-name
```

---

## 4. Working on the project

Make your changes normally.

When you want to save your work to Git:

```bash
git status
```

Add changed files:

```bash
git add .
```

Create a commit:

```bash
git commit -m "Add temperature sensor support"
```

Push your changes to GitHub:

```bash
git push
```

Typical workflow:

```bash
git add .
git commit -m "Description of changes"
git push
```

---