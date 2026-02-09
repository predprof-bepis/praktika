import os

print("Анализ поступления в ВУЗ")
print("[0] GUI")
print("[1] Web")
match input("Ввод:"):
    case "0":
        os.system("python mainscreen.py")
    case "1":
        os.chdir("web")
        os.system("python app.py")
