export interface ExampleType {
    id: number;
    name: string;
    description?: string;
}

export type User = {
    id: string;
    username: string;
    email: string;
    createdAt: Date;
};

export interface Product {
    id: string;
    title: string;
    price: number;
    inStock: boolean;
}

export type ApiResponse<T> = {
    data: T;
    error?: string;
};