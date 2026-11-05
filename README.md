![Banner Image](docs/images/banner.png)

# `dsai` - Data Science and AI for Systems Engineering

*Course repository for SYSEN 5381: Data Science and AI for Systems Engineering*

> This repository contains code and exercises for the course **Data Science and AI for Systems Engineering**, henceforth **DSAI**. Students will build skills for modern **AI** applications using **APIs** and **Apps**.

> You may use **Python**, **R**, or another language/framework of your choosing. Lessons and starter code are provided in R and/or Python. You may even mix and match at times, writing an **API** in Python and an **App** in R, etc.

---

## 📚 QUICK LINKS

- [SCHEDULE](docs/READ_schedule.md)
- [CANVAS](https://canvas.cornell.edu/courses/81764)
- [SYLLABUS](#YOUR-SYLLABUS)
- [Questions?](#-questions)

---

### 🎯 ABOUT THIS COURSE

Modern engineering systems increasingly rely on cloud-based, AI-driven data processing, automation, and analytics. This course equips Systems Engineering students with the coding skills needed to interact with cloud-hosted data, automate workflows, and build scalable AI-powered apps and analytics. Students will gain hands-on experience in querying web APIs, building APIs, and leveraging AI models for automation. Topics include API calls, querying Generative AI, and automation, all to serve automated data reporting. Participants will learn to examine and critique uses of AI in modern systems, considering risk, value, tradeoffs, and policy issues for the customer and society. By the end of the course, students will have built cloud-hosted, AI-powered applications and reporting systems that can dynamically retrieve, process, and visualize data using generative AI. Students are expected to spend 3-4 hours per week per credit hour. Intended for graduate students performing technical tasks interested in software development or data analytics.

## 📋 YOUR SYLLABUS

See course details in the [`docs/`](docs/) folder! Includes:

- [📌 READ: Course Details](docs/READ_course_details.md)
- [📌 READ: Course Assignments](docs/READ_assignments.md)
    - [Assignment Breakdown](docs/READ_assignments.md#-assignment-breakdown)
    - [Grading Practices and Policies](docs/READ_assignments.md#-grading-practices-and-policies)
    - [Grading Scale](docs/READ_assignments.md#-grading-scale)
- [📌 READ: Course Materials](docs/READ_course_materials.md)
    - [Readings](docs/READ_course_materials.md#-readings)
    - [Software](docs/READ_course_materials.md#-software)
- [📌 READ: Course Schedule](docs/READ_schedule.md)


<!-- book:start -->
## 📘 Course book

The course book is live at [https://connect.systems-apps.com/dsai/](https://connect.systems-apps.com/dsai/): 23 modules, each with its page and the kit folder that goes with it.

- Module 1: Set up, and query your first API · [page](https://connect.systems-apps.com/dsai/modules/module-01/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-01)
- Module 2: Productivity with AI · [page](https://connect.systems-apps.com/dsai/modules/module-02/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-02)
- Module 3: AI as an API, and evals · [page](https://connect.systems-apps.com/dsai/modules/module-03/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-03)
- Module 4: Deployment · [page](https://connect.systems-apps.com/dsai/modules/module-04/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-04)
- Module 5: Function calling, agents with tools, and your first MCP server · [page](https://connect.systems-apps.com/dsai/modules/module-05/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-05)
- Module 6: Data management · [page](https://connect.systems-apps.com/dsai/modules/module-06/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-06)
- Module 7: RAG: retrieval-augmented generation, and alternatives · [page](https://connect.systems-apps.com/dsai/modules/module-07/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-07)
- Module 8: Agents: prompts, roles, rules, many agents · [page](https://connect.systems-apps.com/dsai/modules/module-08/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-08)
- Module 9: Pipelines and cron · [page](https://connect.systems-apps.com/dsai/modules/module-09/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-09)
- Module 10: AI in the browser · [page](https://connect.systems-apps.com/dsai/modules/module-10/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-10)
- Module 11: Evaluation · [page](https://connect.systems-apps.com/dsai/modules/module-11/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-11)
- Module 12: Better user interfaces · [page](https://connect.systems-apps.com/dsai/modules/module-12/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-12)
- Module 13: Decision support · [page](https://connect.systems-apps.com/dsai/modules/module-13/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-13)
- Module 14: Hackathon · [page](https://connect.systems-apps.com/dsai/modules/module-14/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-14)
- Module 15: A bounded autonomous agent over HTTP · [page](https://connect.systems-apps.com/dsai/modules/module-15/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-15)
- Module 16: Local agents: a small model, a strict contract, a real job · [page](https://connect.systems-apps.com/dsai/modules/module-16/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-16)
- Module 17: Vision models · [page](https://connect.systems-apps.com/dsai/modules/module-17/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-17)
- Module 18: Audio models: listen, transcribe, speak · [page](https://connect.systems-apps.com/dsai/modules/module-18/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-18)
- Module 19: Geo LLMs: addresses, parcels, places · [page](https://connect.systems-apps.com/dsai/modules/module-19/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-19)
- Module 20: Models on your phone · [page](https://connect.systems-apps.com/dsai/modules/module-20/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-20)
- Module 21: APIs that sleep: scale to zero · [page](https://connect.systems-apps.com/dsai/modules/module-21/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-21)
- Module 22: Data architecture: where each piece of data lives · [page](https://connect.systems-apps.com/dsai/modules/module-22/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-22)
- Module 23: Finale · [page](https://connect.systems-apps.com/dsai/modules/module-23/) · [kit](https://github.com/timothyfraser/dsai/tree/v2027/kit/module-23)
<!-- book:end -->

## 🧱 Course folders (2026)

- [00_quickstart](00_quickstart/)
- [01_query_api](01_query_api/)
- [02_productivity](02_productivity/)
- [03_query_ai](03_query_ai/)
- [04_deployment](04_deployment/)
- [05_hackathon](05_hackathon/)
- [06_agents](06_agents/)
- [07_rag](07_rag/)
- [08_function_calling](08_function_calling/)
- [09_text_analysis](09_text_analysis/)
- [10_data_management](10_data_management/)
- [11_decision_support](11_decision_support/)
- [12_end](12_end/)
- [docs](docs/)

---





# 💬 Questions?

Reach out via Canvas or use EdDiscussion. You're not expected to know everything upfront — the point is to **try**, **fail**, **fix**, and **learn**!

---

![](docs/images/icons.png)

---

← 🏠 [Back to Top](#Table-of-Contents)