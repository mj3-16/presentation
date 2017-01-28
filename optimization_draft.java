class Test {

	public boolean run(){
		int size = 10;
		int[] result = createArray(size, size * 3 + 4);
		return result[0] == size * 3 + 4;
	}
	
	public int[] createArray(int size, int value){
		int[] arr = new int[size];
		arr[0] = value;
		return arr;
	}
}

after common sub expression elemination

class Test {

	public boolean run(){
		int size = 10;
		int imm1 = size * 3 + 4;
		int[] result = createArray(size, imm1);
		return result[0] == imm1;
	}
	
	public int[] createArray(int size, int value){
		int[] arr = new int[size];
		arr[0] = value;
		return arr;
	}
}

after contant folding:

class Test {

	public boolean run(){

		int[] result = createArray(10, 34);
		return result[0] == 34;
	}
	
	public int[] createArray(int size, int value){
		int[] arr = new int[size];
		arr[0] = value;
		return arr;
	}
}

after inlining

class Test {

	public boolean run(){
		int[] arr = new int[10];
		arr[0] = 34;
		return arr[0] == 34;
	}
}

after alias analysis

class Test {

	public boolean run(){
		return 34 == 34;
	}
}

after constant propagation

class Test {

	public boolean run(){
		return true;
	}
}
