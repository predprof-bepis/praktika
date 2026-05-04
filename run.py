import os

print("Анализ поступления в ВУЗ")
print("[1] Web")
match input("Ввод:"):
    case "1":
        os.chdir("web")
        os.system("python app.py")
