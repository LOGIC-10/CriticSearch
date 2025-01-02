from typing import Dict

from critic_search.tools.search_adapter.db.database import recreate_db

from .base_agent import BaseAgent
from .config import settings
from .log import colorize_message, logger, set_logger_level_from_config


def log_iteration_info(
    iteration_number: int, all_search_queries: str, final_agent_answer: str
):
    """记录当前迭代的信息。"""
    colorize_message(message_title=f"TOTAL ITERATIONS: {iteration_number}", color="red")

    colorize_message(
        message_title="ALL SEARCH QUERIES",
        message_content=all_search_queries,
    )
    colorize_message(
        message_title="FINAL ANSWER",
        color="red",
        message_content=final_agent_answer,
    )


def get_agent_answer_with_plan(
    user_task: str,
    plan_template_name: str,
    **plan_kwargs,  # 额外的关键字参数，灵活打包
) -> tuple[str, str]:
    # 1) 生成 search_plan
    # 由调用端决定要不要传入 previous_answer、user_feedback、search_history 等
    search_plan = BaseAgent.chat_with_template(
        template_name=plan_template_name, user_question=user_task, **plan_kwargs
    )

    # 2) 使用 web_scraper 得到爬取结果
    search_results = BaseAgent.chat_with_template(
        template_name="web_scraper",
        user_question=user_task,
        initial_search_results=search_plan,
    )

    assert isinstance(search_results, str), (
        f"Expected 'search_results' to be str, but got '{type(search_results).__name__}'. "
        f"Partial content: {repr(str(search_results)[:200])}"
    )

    # 3) 根据爬取结果生成最终答案
    agent_answer = BaseAgent.chat_with_template(
        template_name="rag_based_answer",
        user_question=user_task,
        web_result_markdown_text=search_results,
        use_tool=False,
    )

    assert isinstance(agent_answer, str)
    assert isinstance(search_plan, str)

    return agent_answer, search_plan


def main(user_task: str, max_iterations: int):
    """Main function to handle the agent's iterative process."""

    set_logger_level_from_config(log_level=settings.log_level.upper())

    logger.success(f"Start to process Task: '{user_task}'")

    BaseAgent.conversation_manager.append_to_history(role="user", content=user_task)

    for iteration in range(1, max_iterations + 1):
        if iteration == 1:
            colorize_message(
                message_title=f"ITERATION {iteration}",
                color="cyan",
                style="bold",
            )

            # Step 1: Confidence check
            confidence_response = BaseAgent.chat_with_template(
                template_name="model_confidence",
                user_question=user_task,
                use_tool=False,
            )

            colorize_message(message_content=confidence_response)

            assert isinstance(
                confidence_response, Dict
            ), f"Expected a dict, got {type(confidence_response).__name__}."

            is_confident = (
                confidence_response.get("confidence", "true").lower() == "true"
            )

            if is_confident:
                # 如果模型有信心，直接生成答案
                agent_answer = BaseAgent.common_chat(
                    usr_prompt=user_task, use_tool=False
                )
            else:
                # 如果模型不自信，生成初始搜索计划并获取答案
                agent_answer, search_plan = get_agent_answer_with_plan(
                    user_task=user_task,
                    plan_template_name="planner_agent_initial_search_plan",
                )
        else:
            # 后续迭代：基于之前的答案和反馈更新答案
            agent_answer = BaseAgent.chat_with_template(
                template_name="agent_update_answer",
                query=user_task,
                previous_answer=agent_answer,
                search_results=search_plan,
                critic_feedback=critic_feedback,
                use_tool=False,
            )

        # 获取评论反馈
        critic_feedback = BaseAgent.chat_with_template(
            template_name="critic_agent",
            user_question=user_task,
            agent_answer=agent_answer,
            use_tool=False,
            role="critic",
        )

        assert isinstance(critic_feedback, Dict)

        if critic_feedback.get("Stop", "").lower() == "true":
            logger.success("Critic feedback indicates stopping the conversation.")

            assert isinstance(agent_answer, str)

            log_iteration_info(
                iteration, BaseAgent.get_all_history_queries(), agent_answer
            )

            break

        # 生成带有反思的搜索计划并获取新的答案
        agent_answer, search_plan = get_agent_answer_with_plan(
            user_task=user_task,
            plan_template_name="planner_agent_with_reflection",
            previous_answer=agent_answer,
            user_feedback=critic_feedback,
            search_history=BaseAgent.get_all_history_queries(),
        )

        # 记录当前迭代的信息
        log_iteration_info(
            iteration_number=iteration,
            all_search_queries=BaseAgent.get_all_history_queries(),
            final_agent_answer=agent_answer,
        )

    logger.success("Conversation ended.")
    recreate_db()
