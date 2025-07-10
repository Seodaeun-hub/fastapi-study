def solution(s):
    answer=list(map(int,s.split()))
    return(f"{min(answer)} {max(answer)}")

# def solution(s):
#     s = list(map(int,s.split()))
#     return str(min(s)) + " " + str(max(s))

#문자열을 숫자형으로 바꾸고 싶을 때는 list(map(int,s.split()))를 사용해서 숫자형으로 바꾼 list를 생성한다.
#최솟값과 최댓값을 찾을 때는 문자열을 숫자형으로 바꾼 후 찾아야한다.
#첫 번째 방법 : return(f"{} {} {}")-> 이렇게 사용하면 공백으로 연결된 문자열로 변환할 수 있다.
#두 번째 방법 : str로 바꿔서 더해주면 된다.