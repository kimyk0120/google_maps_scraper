import json
import sys

from scraper import scraper
import argparse

if __name__ == '__main__':
    # Argument Parser 생성
    parser = argparse.ArgumentParser(description="Search keyword for scraper.")

    # 커맨드라인에서 받을 argument 추가
    parser.add_argument(
        "keyword",
        type=str,
        help="Search keyword to be used by the scraper."
    )

    # 출력 파일 경로 (선택 인자, 기본값 제공)
    parser.add_argument(
        "--output",
        type=str,
        default="./output/output.json",  # 출력 파일 기본값 설정
        help="Path for saving the scraper output (default: 'output.txt')."
    )

    # 파라미터 파싱
    args = parser.parse_args()

    # 유효성 검사: keyword가 제공되지 않았을 경우 에러 처리
    if not args.keyword:
        print("Error: Please provide a search keyword as the first argument.")
        sys.exit(1)  # 오류 코드 1로 종료

    data_result = scraper.main(args.keyword)
    json_data = json.dumps(data_result, ensure_ascii=False, indent=4)

    # 결과를 파일로 저장
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_data)
        print(f"Output successfully written to {args.output}")
    except Exception as e:
        print(f"Error writing to file {args.output}: {e}")
        sys.exit(1)  # 에러 발생 시 종료


