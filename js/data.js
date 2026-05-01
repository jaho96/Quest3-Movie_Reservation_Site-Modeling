// Mock data based on DB modeling

const DB = {
  customers: [
    { id: 1, name: '김민준', email: 'minjun@email.com', phone: '010-1234-5678', birth: '1995-03-15', type: '회원', status: '정상' }
  ],

  movies: [
    {
      id: 1, title: '베테랑 2', originalTitle: 'Veteran 2', subtitle: '',
      synopsis: '광역수사대 형사 서도철이 또다시 거대한 악과 맞닥뜨린다. 거침없고 무모하지만 정의로운 그의 수사가 다시 시작된다.',
      summary: '정의로운 형사 서도철의 두 번째 이야기',
      genre: '액션', rating: '15세', screenType: '2D', ratingLevel: '폭력성',
      runtime: 109, releaseDate: '2024-09-13', bookingRate: 32.5,
      cumAudience: 7630000,
      poster: 'https://via.placeholder.com/300x430/1a1a2e/e94560?text=베테랑2',
      director: '류승완', cast: '황정민, 정해인, 오달수', writer: '류승완',
      country: '한국', status: '상영중',
      genre_tags: ['액션', '범죄'],
      awards: '2024 청룡영화상 최우수작품상'
    },
    {
      id: 2, title: '인사이드 아웃 2', originalTitle: 'Inside Out 2', subtitle: '',
      synopsis: '라일리의 새로운 감정들이 등장하면서 벌어지는 이야기. 불안이라는 새로운 감정이 주인공으로 등장한다.',
      summary: '새로운 감정 불안과 함께하는 라일리의 성장 이야기',
      genre: '애니메이션', rating: '전체관람가', screenType: '2D/3D', ratingLevel: '없음',
      runtime: 100, releaseDate: '2024-06-12', bookingRate: 18.2,
      cumAudience: 5900000,
      poster: 'https://via.placeholder.com/300x430/0f3460/e94560?text=인사이드+아웃2',
      director: 'Kelsey Mann', cast: '에이미 포얼러, 마야 호크', writer: 'Dave Holstein',
      country: '미국', status: '상영중',
      genre_tags: ['애니메이션', '가족'],
      awards: ''
    },
    {
      id: 3, title: '파묘', originalTitle: 'Exhuma', subtitle: '',
      synopsis: '거액의 의뢰를 받은 무당과 장의사가 수상한 묫자리를 이장하면서 벌어지는 이야기.',
      summary: '이장 작업에서 시작된 기이한 사건들',
      genre: '공포', rating: '15세', screenType: '2D', ratingLevel: '공포',
      runtime: 134, releaseDate: '2024-02-22', bookingRate: 8.1,
      cumAudience: 11920000,
      poster: 'https://via.placeholder.com/300x430/16213e/e94560?text=파묘',
      director: '장재현', cast: '최민식, 유해진, 김고은, 이도현', writer: '장재현',
      country: '한국', status: '상영중',
      genre_tags: ['공포', '미스터리'],
      awards: '2024 대종상 최우수작품상'
    },
    {
      id: 4, title: '듄: 파트 2', originalTitle: 'Dune: Part Two', subtitle: '',
      synopsis: '폴 아트레이데스는 샤이 훌루드를 타며 프레멘의 예언자로 거듭나고, 황제에게 복수하기 위한 전쟁을 시작한다.',
      summary: '폴의 복수와 예언자로서의 여정',
      genre: 'SF', rating: '12세', screenType: '2D/3D/IMAX', ratingLevel: '없음',
      runtime: 165, releaseDate: '2024-02-28', bookingRate: 12.3,
      cumAudience: 4200000,
      poster: 'https://via.placeholder.com/300x430/533483/e94560?text=듄파트2',
      director: '드니 빌뇌브', cast: '티모시 샬라메, 젠데이아, 오스틴 버틀러', writer: '드니 빌뇌브',
      country: '미국', status: '상영중',
      genre_tags: ['SF', '어드벤처'],
      awards: '2024 아카데미 최우수촬영상'
    },
    {
      id: 5, title: '하이재킹', originalTitle: 'Hijack 1971', subtitle: '',
      synopsis: '1971년 실제로 발생한 대한항공 납치 사건을 바탕으로 한 영화. 죽음과 맞바꾼 용기로 승객을 지키려는 승무원들의 이야기.',
      summary: '1971년 실화 기반 항공기 납치 사건',
      genre: '액션', rating: '15세', screenType: '2D', ratingLevel: '폭력성',
      runtime: 100, releaseDate: '2024-06-21', bookingRate: 15.7,
      cumAudience: 3100000,
      poster: 'https://via.placeholder.com/300x430/1a1a2e/16213e?text=하이재킹',
      director: '류승완', cast: '하정우, 여진구, 성동일', writer: '류승완',
      country: '한국', status: '상영중',
      genre_tags: ['액션', '드라마'],
      awards: ''
    },
    {
      id: 6, title: '위키드', originalTitle: 'Wicked', subtitle: '',
      synopsis: '오즈의 마법사 이전 이야기. 착한 마녀 글린다와 훗날 나쁜 마녀가 되는 엘파바의 우정과 갈등을 다룬다.',
      summary: '오즈의 마법사 세계관 속 두 마녀의 우정',
      genre: '뮤지컬', rating: '전체관람가', screenType: '2D', ratingLevel: '없음',
      runtime: 160, releaseDate: '2024-11-22', bookingRate: 22.4,
      cumAudience: 890000,
      poster: 'https://via.placeholder.com/300x430/2d1b69/e94560?text=위키드',
      director: '존 M. 추', cast: '신시아 에리보, 아리아나 그란데', writer: '위닌 홀즈만',
      country: '미국', status: '상영중',
      genre_tags: ['뮤지컬', '판타지'],
      awards: ''
    }
  ],

  theaters: [
    { id: 1, name: 'CGV 강남', region: '서울', addressId: 1, info: '강남역 근처 프리미엄 극장', transport: '지하철 2호선 강남역 11번 출구', parking: '2시간 무료', status: '운영중', screenCount: 8 },
    { id: 2, name: 'CGV 홍대', region: '서울', addressId: 2, info: '홍대입구역 CGV', transport: '지하철 2호선 홍대입구역 9번 출구', parking: '1시간 무료', status: '운영중', screenCount: 6 },
    { id: 3, name: 'CGV 부산해운대', region: '부산', addressId: 3, info: '해운대 마린시티 CGV', transport: '지하철 2호선 해운대역 3번 출구', parking: '2시간 무료', status: '운영중', screenCount: 7 },
    { id: 4, name: 'CGV 대구동성로', region: '대구', addressId: 4, info: '동성로 CGV 프리미엄', transport: '지하철 1호선 중앙로역', parking: '제한 없음', status: '운영중', screenCount: 5 },
    { id: 5, name: 'CGV 인천', region: '인천', addressId: 5, info: '인천 CGV', transport: '지하철 1호선 부평역', parking: '2시간 무료', status: '운영중', screenCount: 6 }
  ],

  screens: [
    { id: 1, theaterId: 1, classification: '일반관', number: 1, floor: 3, seatCount: 150, status: '운영중' },
    { id: 2, theaterId: 1, classification: '특별관', number: 2, floor: 4, seatCount: 80, status: '운영중' },
    { id: 3, theaterId: 1, classification: 'IMAX', number: 3, floor: 5, seatCount: 200, status: '운영중' },
    { id: 4, theaterId: 2, classification: '일반관', number: 1, floor: 2, seatCount: 120, status: '운영중' },
    { id: 5, theaterId: 2, classification: '특별관', number: 2, floor: 3, seatCount: 90, status: '운영중' },
    { id: 6, theaterId: 3, classification: '일반관', number: 1, floor: 2, seatCount: 130, status: '운영중' },
    { id: 7, theaterId: 4, classification: '일반관', number: 1, floor: 2, seatCount: 140, status: '운영중' },
    { id: 8, theaterId: 5, classification: '일반관', number: 1, floor: 2, seatCount: 120, status: '운영중' }
  ],

  schedules: [
    // 베테랑 2 - CGV 강남
    { id: 1, theaterId: 1, screenId: 1, movieId: 1, date: '2026-05-01', startTime: '09:00', endTime: '10:49', timeSlot: '조조', round: 1, status: '상영예정' },
    { id: 2, theaterId: 1, screenId: 1, movieId: 1, date: '2026-05-01', startTime: '12:30', endTime: '14:19', timeSlot: '일반', round: 2, status: '상영예정' },
    { id: 3, theaterId: 1, screenId: 2, movieId: 1, date: '2026-05-01', startTime: '15:00', endTime: '16:49', timeSlot: '일반', round: 3, status: '상영예정' },
    { id: 4, theaterId: 1, screenId: 1, movieId: 1, date: '2026-05-01', startTime: '20:00', endTime: '21:49', timeSlot: '일반', round: 4, status: '상영예정' },
    { id: 5, theaterId: 1, screenId: 2, movieId: 1, date: '2026-05-01', startTime: '23:30', endTime: '01:19', timeSlot: '심야', round: 5, status: '상영예정' },
    // 인사이드 아웃 2 - CGV 강남
    { id: 6, theaterId: 1, screenId: 1, movieId: 2, date: '2026-05-01', startTime: '10:00', endTime: '11:40', timeSlot: '일반', round: 1, status: '상영예정' },
    { id: 7, theaterId: 1, screenId: 3, movieId: 2, date: '2026-05-01', startTime: '14:00', endTime: '15:40', timeSlot: '일반', round: 2, status: '상영예정' },
    // 파묘 - CGV 강남
    { id: 8, theaterId: 1, screenId: 2, movieId: 3, date: '2026-05-01', startTime: '11:00', endTime: '13:14', timeSlot: '일반', round: 1, status: '상영예정' },
    { id: 9, theaterId: 1, screenId: 1, movieId: 3, date: '2026-05-01', startTime: '18:00', endTime: '20:14', timeSlot: '일반', round: 2, status: '상영예정' },
    // 베테랑 2 - CGV 홍대
    { id: 10, theaterId: 2, screenId: 4, movieId: 1, date: '2026-05-01', startTime: '10:30', endTime: '12:19', timeSlot: '일반', round: 1, status: '상영예정' },
    { id: 11, theaterId: 2, screenId: 4, movieId: 1, date: '2026-05-01', startTime: '16:00', endTime: '17:49', timeSlot: '일반', round: 2, status: '상영예정' },
    // 위키드 - CGV 강남
    { id: 12, theaterId: 1, screenId: 3, movieId: 6, date: '2026-05-01', startTime: '13:00', endTime: '15:40', timeSlot: '일반', round: 1, status: '상영예정' },
    { id: 13, theaterId: 1, screenId: 3, movieId: 6, date: '2026-05-01', startTime: '19:00', endTime: '21:40', timeSlot: '일반', round: 2, status: '상영예정' },
    // 날짜 다른것들
    { id: 14, theaterId: 1, screenId: 1, movieId: 1, date: '2026-05-02', startTime: '09:00', endTime: '10:49', timeSlot: '조조', round: 1, status: '상영예정' },
    { id: 15, theaterId: 1, screenId: 1, movieId: 1, date: '2026-05-02', startTime: '14:00', endTime: '15:49', timeSlot: '일반', round: 2, status: '상영예정' },
    { id: 16, theaterId: 1, screenId: 2, movieId: 2, date: '2026-05-02', startTime: '11:00', endTime: '12:40', timeSlot: '일반', round: 1, status: '상영예정' },
    { id: 17, theaterId: 2, screenId: 5, movieId: 4, date: '2026-05-01', startTime: '13:00', endTime: '15:45', timeSlot: '일반', round: 1, status: '상영예정' },
    { id: 18, theaterId: 2, screenId: 5, movieId: 4, date: '2026-05-01', startTime: '18:00', endTime: '20:45', timeSlot: '일반', round: 2, status: '상영예정' }
  ],

  reviews: [
    { id: 1, customerId: 1, movieId: 1, rating: 9, viewingPoints: ['연출', '배우'], content: '황정민 연기가 정말 압도적이었습니다! 속편이지만 전편보다 낫네요.', likes: 234, createdAt: '2024-09-20', status: '정상' },
    { id: 2, customerId: 1, movieId: 1, rating: 8, viewingPoints: ['스토리', 'ost'], content: '시원한 액션과 묵직한 메시지가 잘 조화됩니다.', likes: 189, createdAt: '2024-09-18', status: '정상' },
    { id: 3, customerId: 1, movieId: 3, rating: 10, viewingPoints: ['연출', '스토리', '영상미'], content: '한국 공포영화의 새로운 지평을 열었다고 생각해요. 최민식 배우 진짜 무서웠어요.', likes: 456, createdAt: '2024-03-01', status: '정상' },
    { id: 4, customerId: 1, movieId: 2, rating: 9, viewingPoints: ['스토리', '영상미', '배우'], content: '아이도 어른도 함께 볼 수 있는 감동적인 애니메이션입니다.', likes: 312, createdAt: '2024-06-20', status: '정상' },
    { id: 5, customerId: 1, movieId: 4, rating: 9, viewingPoints: ['연출', '영상미'], content: 'IMAX로 봐야 진가를 느낄 수 있는 영화. 영상미가 정말 최고입니다.', likes: 267, createdAt: '2024-03-05', status: '정상' },
    { id: 6, customerId: 1, movieId: 6, rating: 8, viewingPoints: ['배우', 'ost'], content: '아리아나 그란데와 신시아 에리보의 케미가 대박. 뮤지컬 팬이라면 필수 관람!', likes: 198, createdAt: '2024-11-25', status: '정상' }
  ],

  addresses: [
    { id: 1, postal: '06234', region: '강남구', detail: '지하 1층', road: '서울 강남구 강남대로 438', lot: '서울 강남구 역삼동 832' },
    { id: 2, postal: '04066', region: '마포구', detail: '2층', road: '서울 마포구 양화로 188', lot: '서울 마포구 동교동 147-3' },
    { id: 3, postal: '48095', region: '해운대구', detail: '3층', road: '부산 해운대구 마린시티 2로 33', lot: '부산 해운대구 우동 725' },
    { id: 4, postal: '41940', region: '중구', detail: '2층', road: '대구 중구 중앙대로 407', lot: '대구 중구 동성로 2-3' },
    { id: 5, postal: '21577', region: '부평구', detail: '5층', road: '인천 부평구 부평대로 33', lot: '인천 부평구 부평동 555' }
  ],

  reservations: [
    { id: 1, scheduleId: 1, customerId: 1, reservationNo: 'CGV202409001', date: '2024-09-20', viewers: 2, viewerType: '성인', price: 28000, status: '예매완료' }
  ],

  payments: [
    { id: 1, reservationId: 1, paymentNo: 'PAY202409001', coupon: null, couponType: null, couponStatus: null, points: 500, payMethod: '신용카드', cardCompany: '삼성카드', amount: 27500, status: '결제완료', type: '결제' }
  ],

  tickets: [
    { id: 1, reservationId: 1, seatNo: 'G7', amount: 14000, issuedAt: '2024-09-20', status: '사용완료' },
    { id: 2, reservationId: 1, seatNo: 'G8', amount: 14000, issuedAt: '2024-09-20', status: '사용완료' }
  ],

  prices: {
    adult: 14000,
    teen: 11000,
    senior: 9000,
    special: 3000,
    imax: 5000
  }
};

// 현재 로그인 상태 (mock)
let currentUser = null;
let bookingSession = {};
