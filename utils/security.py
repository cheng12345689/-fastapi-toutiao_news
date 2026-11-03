"""密码安全相关工具：集中管理哈希上下文，供注册/登录等业务调用。"""

from passlib.context import CryptContext

# 密码哈希上下文（整个项目唯一的实例，避免各处重复创建）
# schemes：
#   - 第一个 bcrypt 是默认算法，新密码都用它（自带随机盐，cost=12，越算越慢，抗爆破）
#   - 第二个 pbkdf2_sha256 只用于校验 passlib 格式的历史哈希（$pbkdf2-sha256$...）；
#     项目早期自定义的 pbkdf2_sha256$迭代次数$盐$摘要 格式不兼容，verify 会返回 False
# deprecated="auto"：把非默认算法标记为“可升级”，以后可在登录时用 needs_update() 自动重哈希
pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """把明文密码哈希成可入库的字符串（bcrypt 结果约 60 字符）。

    哈希不可逆，数据库泄露也拿不到原始密码；每个密码的盐随机，
    相同密码两次哈希的结果也不一样。

    注意：bcrypt 只处理前 72 字节，超长密码会被静默截断（4.x 的行为），
    建议在 schema 层就限制密码长度。
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """校验明文密码与数据库中的哈希是否匹配。

    哈希里已经带了算法、盐和参数，所以直接交给上下文比对即可。
    遇到无法识别的格式（比如旧版自定义 pbkdf2 字符串、脏数据）返回 False，
    避免登录接口抛异常变成 500。
    """
    try:
        return pwd_context.verify(password, hashed)
    except ValueError:
        return False
# 密码认证
def veritfy_password(password: str) -> str:
    return pwd_context.verify(password, hash_password(password))