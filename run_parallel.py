import multiprocessing
import bot
import main
import schedule
import time

def run_bot():
    bot.start_bot()

def run_scheduled_updates():
    print("Начата задача по расписанию.")
    schedule.every().day.at("10:00").do(main.main)
    main.main()
    print("Ожидание выполнения задачи.")
    while True:
        schedule.run_pending()
        time.sleep(30)
    print("Задача выполнена.")

def run_parallel():
    process1 = multiprocessing.Process(target=run_bot)
    process2 = multiprocessing.Process(target=run_scheduled_updates)

    process1.start()
    process2.start()

    process1.join()
    process2.join()

if __name__ == "__main__":
    run_parallel()

